import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel

import logging
import time

from vector_store import process_and_store_document
from rag_app import vectorstore, prompt_template, llm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Lab API",
    description="Backend service for document vectorization and grounded Q&A.",
    version="1.0.0"
)

# Enable CORS so the browser frontend can talk to FastAPI without security blocks
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    document_name: Optional[str] = None


ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".csv", ".json"}


@app.get("/api/v1/health")
def health_check():
    """Health check endpoint to verify backend status."""
    return {"status": "online", "message": "RAG API server is running."}


@app.post("/api/v1/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Endpoint to receive a document over HTTP, save it temporarily,
    and process its vectors into ChromaDB.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_uploads")
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, file.filename)

    try:
        # Save uploaded file stream to disk temporarily
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Vectorize and embed into ChromaDB
        process_and_store_document(temp_file_path, original_filename=file.filename)

        return {
            "status": "success",
            "filename": file.filename,
            "message": "File successfully embedded and saved into ChromaDB."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")
    finally:
        # Clean up temporary upload file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.post("/api/v1/ask")
def ask_question(request: QueryRequest):
    """
    Endpoint to query the RAG pipeline. Searches ChromaDB and returns
    grounded LLM response + retrieved context.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    start_time = time.perf_counter()

    try:
        # 1. Retrieve matching chunks from ChromaDB (filtered to active document if provided)
        if request.document_name:
            matching_docs = vectorstore.similarity_search(
                request.question,
                k=8,
                filter={"source": request.document_name}
            )
            # If no chunks matched specific filter, fallback to general search
            if not matching_docs:
                matching_docs = vectorstore.similarity_search(request.question, k=8)
        else:
            matching_docs = vectorstore.similarity_search(request.question, k=8)

        context_text = "\n\n".join([doc.page_content for doc in matching_docs])

        # 2. Extract source citations (convert 0-indexed page to 1-indexed for display)
        sources = [
            {
                "source": doc.metadata.get("source"),
                "page": doc.metadata.get("page") + 1 if doc.metadata.get("page") is not None else None,
            }
            for doc in matching_docs
        ]

        # 3. Format prompt template
        formatted_messages = prompt_template.format_prompt(
            context=context_text,
            question=request.question
        ).to_messages()

        # 4. Generate answer via LLM
        response = llm.invoke(formatted_messages)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"Answered question={request.question!r} sources={len(sources)} elapsed_ms={elapsed_ms:.1f}")

        return {
            "question": request.question,
            "answer": response.content,
            "sources": sources,
            "context_retrieved": [doc.page_content for doc in matching_docs]
        }
    except Exception as e:
        logger.exception(f"LLM generation error for question: {request.question!r}")
        raise HTTPException(status_code=500, detail=f"LLM generation error: {str(e)}")