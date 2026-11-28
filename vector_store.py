import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


CHROMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")


def process_and_store_document(file_path: str, original_filename: str = None):
    """
    Loads a PDF, TXT, MD, DOCX, CSV, or JSON file, splits it into overlapping chunks,
    generates embeddings, and persists them into ChromaDB.

    Re-running this on the same file_path replaces that file's old
    chunks instead of duplicating them, so ingestion is idempotent.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    display_name = original_filename or os.path.basename(file_path)
    print(f"\n1. Loading document: {display_name} from: {file_path}")

    # Select loader based on file extension
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext in [".txt", ".md", ".json"]:
        loader = TextLoader(file_path, autodetect_encoding=True)
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)
    elif ext == ".csv":
        loader = CSVLoader(file_path)
    else:
        raise ValueError(f"Unsupported file format '{ext}'. Supported formats: .pdf, .txt, .md, .docx, .csv, .json")

    raw_documents = loader.load()
    print(f"Loaded {len(raw_documents)} raw page(s)/document(s).")

    # Clean metadata so source is always the clean filename, not a temporary path
    for doc in raw_documents:
        doc.metadata["source"] = display_name

    # 2. CHUNKING CONFIGURATION
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len
    )
    chunks = text_splitter.split_documents(raw_documents)
    print(f"2. Created {len(chunks)} text chunks.")

    print("3. Loading embedding model & connecting to ChromaDB...")
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embedding_model
    )

    # DE-DUP GUARD: remove any chunks already in the store from this same source
    existing = vectorstore.get(where={"source": display_name})
    if existing["ids"]:
        print(f"   Found {len(existing['ids'])} existing chunk(s) from this file — replacing them.")
        vectorstore.delete(ids=existing["ids"])

    vectorstore.add_documents(chunks)

    print("Success! Document processed and saved into ChromaDB.\n")
    return vectorstore


if __name__ == "__main__":
    # Sample test - commented out so sample.pdf is not automatically re-ingested into ChromaDB.
    # Uncomment below if you want to manually ingest sample.pdf:
    # sample_file = "sample.pdf"
    # if os.path.exists(sample_file):
    #     process_and_store_document(sample_file)
    # else:
    #     print(f"Place a sample PDF named '{sample_file}' in this directory to test manually!")
    pass