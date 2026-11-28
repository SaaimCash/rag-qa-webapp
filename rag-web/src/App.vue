<template>
  <div class="app-layout">
    <!-- TOP NAVIGATION BAR -->
    <header class="top-nav">
      <div class="brand">
        <div class="brand-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
          </svg>
        </div>
        <div>
          <h1 class="brand-title">Document Rag App</h1>
        </div>
      </div>

      <div class="nav-actions">
        <div class="status-indicator" :class="{ online: backendOnline, offline: !backendOnline }">
          <span class="status-dot"></span>
          <span class="status-text">{{ backendOnline ? 'Backend Online' : 'Backend Offline' }}</span>
        </div>
      </div>
    </header>

    <!-- MAIN DUAL-PANE WORKSPACE -->
    <main class="workspace-grid">
      <!-- LEFT PANE: DOCUMENT VIEWER & UPLOADER ("HOLD THE PDF") -->
      <section class="pane doc-pane">
        <div class="pane-header">
          <div class="pane-title-group">
            <div>
              <h2 class="pane-title">Document Viewer</h2>
              <span class="pane-subtitle" v-if="activeDoc">{{ activeDoc.name }}</span>
              <span class="pane-subtitle" v-else>No document loaded yet</span>
            </div>
          </div>

          <div class="header-buttons" v-if="activeDoc?.previewUrl">
            <a
              :href="activeDoc.previewUrl"
              target="_blank"
              rel="noopener"
              class="icon-btn"
              title="Open document in new tab"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                <polyline points="15 3 21 3 21 9"></polyline>
                <line x1="10" y1="14" x2="21" y2="3"></line>
              </svg>
              <span>Popout</span>
            </a>
          </div>
        </div>

        <!-- UPLOAD SECTION / DROPZONE -->
        <div
          class="dropzone-card"
          :class="{ dragging: isDragging, 'has-file': !!selectedFile }"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
        >
          <input
            id="file-input"
            ref="fileInputRef"
            type="file"
            accept=".pdf,.txt,.md,.docx,.csv,.json,application/pdf"
            class="hidden-file-input"
            @change="handleFileChange"
          />

          <div class="dropzone-content" v-if="!selectedFile && !isUploading">
            <div class="upload-icon-circle">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
            </div>
            <p class="drop-text">
              <strong>Drag & drop your document here</strong> or
              <label for="file-input" class="browse-link">browse files</label>
            </p>
            <p class="drop-hints">Supports PDF, TXT, MD, DOCX, CSV, JSON</p>
          </div>

          <!-- PENDING FILE SELECTION -->
          <div class="pending-file-box" v-else-if="selectedFile">
            <div class="file-info-row">
              <div class="file-icon-badge">{{ getFileExtension(selectedFile.name) }}</div>
              <div class="file-details">
                <span class="file-name">{{ selectedFile.name }}</span>
                <span class="file-size">{{ (selectedFile.size / 1024).toFixed(1) }} KB</span>
              </div>
              <button
                class="remove-btn"
                title="Cancel selection"
                :disabled="isUploading"
                @click="clearSelectedFile"
              >
                ✕
              </button>
            </div>

            <button
              class="btn-primary upload-action-btn"
              :disabled="isUploading"
              @click="uploadDocument"
            >
              <span v-if="isUploading" class="spinner"></span>
              {{ isUploading ? 'Vectorizing and Indexing into ChromaDB...' : 'Ingest Document into RAG' }}
            </button>
          </div>
        </div>

        <!-- NOTIFICATIONS -->
        <div v-if="errorMessage" class="alert alert-error">
          <span class="alert-icon">⚠️</span>
          <span>{{ errorMessage }}</span>
        </div>
        <div v-if="successMessage" class="alert alert-success">
          <span class="alert-icon">✅</span>
          <span>{{ successMessage }}</span>
        </div>

        <!-- DOCUMENT PREVIEW CONTAINER ("HOLD THE PDF") -->
        <div class="preview-container">
          <!-- IF PDF IS ACTIVE: EMBED NATIVE VIEWER -->
          <div v-if="activeDoc && isPdf(activeDoc.name)" class="pdf-viewer-wrapper">
            <iframe
              :src="activeDoc.previewUrl"
              class="pdf-iframe"
              title="PDF Preview"
            ></iframe>
          </div>

          <!-- IF TEXT / MD / JSON IS ACTIVE: SHOW FORMATTED VIEWER -->
          <div v-else-if="activeDoc && textPreviewContent" class="text-viewer-wrapper">
            <div class="text-viewer-header">
              <span>Text Preview (First 50KB)</span>
              <span class="mono">{{ activeDoc.name }}</span>
            </div>
            <pre class="text-content"><code>{{ textPreviewContent }}</code></pre>
          </div>

          <!-- IF OTHER TYPE (DOCX / CSV): SHOW SUMMARY CARD -->
          <div v-else-if="activeDoc" class="doc-card-view">
            <div class="doc-badge-large">{{ getFileExtension(activeDoc.name) }}</div>
            <h3>{{ activeDoc.name }}</h3>
            <p>Document indexed and ready for semantic vector search in ChromaDB.</p>
            <span class="meta-tag">{{ (activeDoc.size / 1024).toFixed(1) }} KB</span>
          </div>

          <!-- EMPTY STATE: NO DOCUMENT LOADED YET -->
          <div v-else class="empty-preview">
            <div class="empty-icon-wrap">
              <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#71717a" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <circle cx="12" cy="14" r="3"></circle>
              </svg>
            </div>
            <h3>No Document Displayed</h3>
            <p>Upload a PDF or document above to preview it here and ground your AI queries in its contents.</p>
          </div>
        </div>
      </section>

      <!-- RIGHT PANE: RAG CHAT CONVERSATION -->
      <section class="pane chat-pane">
        <div class="pane-header">
          <div class="pane-title-group">
            <div>
              <h2 class="pane-title">RAG Q&A Assistant</h2>
            </div>
          </div>

          <button
            v-if="messages.length > 0"
            class="icon-btn text-btn"
            @click="clearChat"
            title="Clear chat history"
          >
            Clear History
          </button>
        </div>

        <!-- CONVERSATION STREAM -->
        <div class="chat-stream" ref="chatStreamRef">
          <!-- WELCOME INTRO MESSAGE -->
          <div class="chat-message assistant-message welcome-box">
            <div class="avatar assistant-avatar"><strong>AI</strong></div>
            <div class="message-body">
              <p class="greeting-heading"><strong>Welcome to your RAG Research Assistant!</strong></p>
              <p>Upload documents on the left panel. When you ask questions here, the pipeline retrieves relevant passages from <strong>ChromaDB</strong> and synthesizes grounded answers with page citations.</p>

              <!-- SUGGESTED PROMPT CHIPS -->
              <div class="starter-chips" v-if="activeDoc">
                <span class="chips-label">Try asking:</span>
                <button
                  class="chip-btn"
                  @click="useSuggestedPrompt('What is the main subject and purpose of this document?')"
                >
                  "What is the main subject of this document?"
                </button>
                <button
                  class="chip-btn"
                  @click="useSuggestedPrompt('Can you summarize the core conclusions and key points?')"
                >
                  "Summarize the core conclusions"
                </button>
              </div>
            </div>
          </div>

          <!-- DYNAMIC MESSAGE LIST -->
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="chat-message"
            :class="msg.role === 'user' ? 'user-message' : 'assistant-message'"
          >
            <div class="avatar" :class="msg.role === 'user' ? 'user-avatar' : 'assistant-avatar'">
              <span v-if="msg.role === 'user'">👤</span>
              <strong v-else>AI</strong>
            </div>

            <div class="message-body">
              <div class="message-bubble">
                <div v-if="msg.role === 'user'" class="text-rendered">{{ msg.text }}</div>
                <div v-else class="text-rendered" v-html="renderMarkdown(msg.text)"></div>
              </div>

              <!-- CITATIONS & CONTEXT EXPANDER (IF AVAILABLE) -->
              <div v-if="msg.sources && msg.sources.length > 0" class="citations-container">
                <div class="citations-header" @click="msg.showContext = !msg.showContext">
                  <span class="citation-tag">
                    📚 Sources:
                    <span v-for="(src, sIdx) in msg.sources" :key="sIdx" class="source-pill">
                      {{ formatSource(src) }}
                    </span>
                  </span>
                  <span class="toggle-link">
                    {{ msg.showContext ? 'Hide Context ▲' : 'Show Retrieved Context ▼' }}
                  </span>
                </div>

                <!-- EXPANDED RETRIEVED CHUNKS -->
                <div v-if="msg.showContext && msg.contextRetrieved" class="context-drawer">
                  <div
                    v-for="(chunk, cIdx) in msg.contextRetrieved"
                    :key="cIdx"
                    class="context-chunk"
                  >
                    <div class="chunk-badge">Chunk #{{ cIdx + 1 }}</div>
                    <pre class="chunk-text">{{ chunk }}</pre>
                  </div>
                </div>
              </div>

              <span class="message-timestamp">{{ msg.time }}</span>
            </div>
          </div>

          <!-- LOADING / GENERATING STATE -->
          <div v-if="isAsking" class="chat-message assistant-message">
            <div class="avatar assistant-avatar"><strong>AI</strong></div>
            <div class="message-body">
              <div class="message-bubble loading-bubble">
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span class="typing-label">Searching ChromaDB & generating grounded response...</span>
              </div>
            </div>
          </div>
        </div>

        <!-- INPUT BAR -->
        <div class="chat-input-bar">
          <textarea
            v-model="inputQuestion"
            class="question-input"
            rows="2"
            placeholder="Ask a question about the uploaded document..."
            :disabled="isAsking"
            @keydown.enter.exact.prevent="submitQuestion"
          ></textarea>

          <button
            class="send-btn"
            :disabled="!inputQuestion.trim() || isAsking"
            @click="submitQuestion"
            title="Send query"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import DOMPurify from 'dompurify'
import { marked } from 'marked'

const API_BASE = 'http://localhost:8000'
const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.md', '.docx', '.csv', '.json']

const renderMarkdown = (text) => DOMPurify.sanitize(marked.parse(text || ''))

// UI & Reactive State
const backendOnline = ref(false)
const fileInputRef = ref(null)
const chatStreamRef = ref(null)

const selectedFile = ref(null)
const activeDoc = ref(null)
const textPreviewContent = ref('')

const isDragging = ref(false)
const isUploading = ref(false)
const isAsking = ref(false)

const errorMessage = ref('')
const successMessage = ref('')
const inputQuestion = ref('')
const messages = ref([])

// Check FastAPI backend status
const checkBackendHealth = async () => {
  try {
    const res = await fetch(`${API_BASE}/api/v1/health`, { method: 'GET' })
    if (res.ok) {
      backendOnline.value = true
    } else {
      backendOnline.value = false
    }
  } catch {
    backendOnline.value = false
  }
}

onMounted(() => {
  checkBackendHealth()
  // Poll health every 15s to keep status fresh
  setInterval(checkBackendHealth, 15000)
})

// File handling
const handleFileChange = (event) => {
  const file = event.target.files[0]
  processSelectedFile(file)
}

const handleDrop = (event) => {
  isDragging.value = false
  const file = event.dataTransfer.files[0]
  processSelectedFile(file)
}

const processSelectedFile = (file) => {
  errorMessage.value = ''
  successMessage.value = ''

  if (!file) {
    selectedFile.value = null
    return
  }

  const ext = '.' + file.name.split('.').pop().toLowerCase()
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    errorMessage.value = `Unsupported file format "${ext}". Supported: ${ALLOWED_EXTENSIONS.join(', ')}`
    selectedFile.value = null
    return
  }

  selectedFile.value = file
}

const clearSelectedFile = () => {
  selectedFile.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
}

const isPdf = (filename) => {
  return filename?.toLowerCase().endsWith('.pdf')
}

const getFileExtension = (filename) => {
  if (!filename) return 'DOC'
  return filename.split('.').pop().toUpperCase()
}

// Upload & Vectorize
const uploadDocument = async () => {
  if (!selectedFile.value) return

  isUploading.value = true
  errorMessage.value = ''
  successMessage.value = ''

  const file = selectedFile.value
  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await fetch(`${API_BASE}/api/v1/upload`, {
      method: 'POST',
      body: formData,
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.detail || 'Upload failed.')
    }

    // Create client-side preview URL for the PDF or text file
    const previewUrl = URL.createObjectURL(file)
    activeDoc.value = {
      name: file.name,
      size: file.size,
      previewUrl,
    }

    // Read initial text preview if text-based
    if (['.txt', '.md', '.json', '.csv'].some((ext) => file.name.toLowerCase().endsWith(ext))) {
      const reader = new FileReader()
      reader.onload = (e) => {
        textPreviewContent.value = e.target.result?.slice(0, 50000) || ''
      }
      reader.readAsText(file)
    } else {
      textPreviewContent.value = ''
    }

    successMessage.value = result.message || `"${file.name}" indexed into ChromaDB successfully!`
    selectedFile.value = null
    if (fileInputRef.value) fileInputRef.value.value = ''
    backendOnline.value = true
  } catch (err) {
    errorMessage.value = 'Ingestion error: ' + err.message
  } finally {
    isUploading.value = false
  }
}

// Chat & RAG Asking
const useSuggestedPrompt = (promptText) => {
  inputQuestion.value = promptText
  submitQuestion()
}

const submitQuestion = async () => {
  const query = inputQuestion.value.trim()
  if (!query || isAsking.value) return

  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  // Push user message
  messages.value.push({
    role: 'user',
    text: query,
    time: now,
  })

  inputQuestion.value = ''
  isAsking.value = true
  await scrollToBottom()

  try {
    const response = await fetch(`${API_BASE}/api/v1/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: query,
        document_name: activeDoc.value?.name || null,
      }),
    })

    const result = await response.json()

    if (!response.ok) {
      throw new Error(result.detail || 'Error generating answer.')
    }

    // Push assistant answer
    messages.value.push({
      role: 'assistant',
      text: result.answer,
      sources: result.sources || [],
      contextRetrieved: result.context_retrieved || [],
      showContext: false,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    })
    backendOnline.value = true
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      text: `⚠️ Query failed: ${err.message}. Please ensure the FastAPI backend is running on port 8000.`,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    })
  } finally {
    isAsking.value = false
    await scrollToBottom()
  }
}

const formatSource = (src) => {
  if (typeof src === 'string') return src
  const name = src.source ? src.source.split(/[/\\]/).pop() : 'Doc'
  const pageStr = src.page !== null && src.page !== undefined ? ` (p. ${src.page})` : ''
  return `${name}${pageStr}`
}

const clearChat = () => {
  messages.value = []
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatStreamRef.value) {
    chatStreamRef.value.scrollTop = chatStreamRef.value.scrollHeight
  }
}
</script>

<style scoped>
/* =========================================================
   BLACK & LIGHT BLACK / WHITE THEME
   - Deepest background: #000000 / #09090b
   - Surface / Panels: #121214
   - Elevated / Lighter Black: #1a1a1e & #222226
   - Borders: #27272a & #323238
   - Text: #ffffff & #a1a1aa
   - Primary Accent: #ffffff (crisp high-contrast monochrome)
========================================================= */

.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background-color: #000000;
  color: #ffffff;
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow: hidden;
  box-sizing: border-box;
}

/* TOP NAVIGATION */
.top-nav {
  height: 60px;
  background-color: #121214;
  border-bottom: 1px solid #232328;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 36px;
  height: 36px;
  background: #222226;
  border: 1px solid #323238;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
}

.brand-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  letter-spacing: -0.02em;
  color: #ffffff;
}

.badge {
  background: #242429;
  color: #ffffff;
  font-size: 0.68rem;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 5px;
  border: 1px solid #383840;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.brand-subtitle {
  font-size: 0.73rem;
  color: #a1a1aa;
  margin: 0;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 500;
  background: #18181c;
  border: 1px solid #2b2b32;
  color: #d4d4d8;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.status-indicator.online .status-dot {
  background-color: #22c55e;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
}

.status-indicator.offline .status-dot {
  background-color: #ef4444;
}

/* DUAL PANE WORKSPACE */
.workspace-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  padding: 14px;
  min-height: 0;
  overflow: hidden;
  background-color: #000000;
}

.pane {
  background-color: #121214;
  border: 1px solid #232328;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
}

.pane-header {
  padding: 12px 18px;
  background-color: #18181b;
  border-bottom: 1px solid #27272a;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.pane-title-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pane-icon {
  font-size: 1.2rem;
}

.pane-title {
  font-size: 0.92rem;
  font-weight: 700;
  margin: 0;
  color: #ffffff;
}

.pane-subtitle {
  font-size: 0.73rem;
  color: #a1a1aa;
  display: block;
}

.icon-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #222226;
  border: 1px solid #33333a;
  color: #ffffff;
  font-size: 0.75rem;
  padding: 5px 11px;
  border-radius: 6px;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.15s ease;
}

.icon-btn:hover {
  background: #ffffff;
  color: #000000;
  border-color: #ffffff;
}

.text-btn {
  font-size: 0.73rem;
}

/* DROPZONE / UPLOADER (LIGHT SHADE OF BLACK) */
.dropzone-card {
  margin: 12px;
  padding: 14px;
  background-color: #1a1a1e;
  border: 1px dashed #3f3f46;
  border-radius: 10px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.dropzone-card.dragging {
  background-color: #24242a;
  border-color: #ffffff;
}

.hidden-file-input {
  display: none;
}

.dropzone-content {
  text-align: center;
  padding: 6px;
}

.upload-icon-circle {
  width: 40px;
  height: 40px;
  background: #25252b;
  border: 1px solid #33333a;
  color: #ffffff;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
}

.drop-text {
  font-size: 0.85rem;
  margin: 4px 0;
  color: #f4f4f5;
}

.browse-link {
  color: #ffffff;
  text-decoration: underline;
  cursor: pointer;
  font-weight: 600;
}

.drop-hints {
  font-size: 0.73rem;
  color: #71717a;
  margin: 2px 0 0;
}

/* PENDING FILE BOX */
.pending-file-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-info-row {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #222226;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid #323238;
}

.file-icon-badge {
  background: #ffffff;
  color: #000000;
  font-size: 0.68rem;
  font-weight: 800;
  padding: 3px 6px;
  border-radius: 4px;
}

.file-details {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.file-name {
  font-size: 0.84rem;
  font-weight: 600;
  color: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 0.7rem;
  color: #a1a1aa;
}

.remove-btn {
  background: none;
  border: none;
  color: #a1a1aa;
  cursor: pointer;
  font-size: 1rem;
  padding: 4px;
}

.remove-btn:hover {
  color: #ffffff;
}

/* PRIMARY BUTTONS: CRISP MONOCHROME WHITE/BLACK */
.btn-primary {
  width: 100%;
  background: #ffffff;
  color: #000000;
  border: none;
  padding: 10px 16px;
  font-size: 0.86rem;
  font-weight: 700;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.15s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #e4e4e7;
  box-shadow: 0 4px 14px rgba(255, 255, 255, 0.15);
}

.btn-primary:disabled {
  background: #27272a;
  color: #71717a;
  cursor: not-allowed;
}

/* ALERTS */
.alert {
  margin: 0 12px 10px;
  padding: 9px 13px;
  border-radius: 7px;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.alert-error {
  background: #261618;
  border: 1px solid #4c2227;
  color: #fca5a5;
}

.alert-success {
  background: #14241a;
  border: 1px solid #21432c;
  color: #86efac;
}

/* PREVIEW CONTAINER ("HOLD THE PDF") */
.preview-container {
  flex: 1;
  margin: 0 12px 12px;
  background-color: #09090b;
  border: 1px solid #232328;
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
  min-height: 0;
}

.pdf-viewer-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: #18181b;
}

.text-viewer-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.text-viewer-header {
  padding: 8px 14px;
  background: #18181b;
  border-bottom: 1px solid #27272a;
  font-size: 0.73rem;
  color: #a1a1aa;
  display: flex;
  justify-content: space-between;
}

.mono {
  font-family: 'JetBrains Mono', monospace;
  color: #ffffff;
}

.text-content {
  flex: 1;
  margin: 0;
  padding: 14px;
  overflow-y: auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  line-height: 1.5;
  color: #d4d4d8;
  white-space: pre-wrap;
  word-break: break-word;
}

.doc-card-view {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 24px;
  text-align: center;
}

.doc-badge-large {
  font-size: 1.4rem;
  font-weight: 800;
  padding: 14px 20px;
  background: #27272a;
  color: #ffffff;
  border: 1px solid #3f3f46;
  border-radius: 12px;
  margin-bottom: 14px;
}

.empty-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 28px;
  text-align: center;
  color: #71717a;
}

.empty-icon-wrap {
  margin-bottom: 12px;
  opacity: 0.6;
}

.empty-preview h3 {
  font-size: 0.95rem;
  font-weight: 600;
  color: #d4d4d8;
  margin: 0 0 6px;
}

.empty-preview p {
  font-size: 0.8rem;
  max-width: 310px;
  line-height: 1.45;
  margin: 0;
  color: #71717a;
}

/* CHAT PANE & STREAM */
.chat-pane {
  display: flex;
  flex-direction: column;
}

.chat-stream {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 0;
  background-color: #121214;
}

.chat-message {
  display: flex;
  gap: 12px;
  max-width: 90%;
  animation: fadeIn 0.15s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.assistant-message {
  align-self: flex-start;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  flex-shrink: 0;
  border: 1px solid #2e2e34;
}

.user-avatar {
  background: #27272a;
}

.assistant-avatar {
  background: #1c1c20;
}

.assistant-avatar strong {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #ffffff;
}

.message-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.message-bubble {
  padding: 11px 15px;
  border-radius: 10px;
  font-size: 0.88rem;
  line-height: 1.55;
  word-break: break-word;
}

.text-rendered :deep(p) {
  margin: 0 0 0.65em;
}

.text-rendered :deep(p:last-child) {
  margin-bottom: 0;
}

.text-rendered :deep(ul),
.text-rendered :deep(ol) {
  margin: 0.4em 0;
  padding-left: 1.5em;
}

.text-rendered :deep(li + li) {
  margin-top: 0.2em;
}

/* USER MESSAGE: ELEVATED LIGHTER BLACK */
.user-message .message-bubble {
  background-color: #27272b;
  color: #ffffff;
  border: 1px solid #383840;
  border-bottom-right-radius: 3px;
}

/* ASSISTANT MESSAGE: LIGHT BLACK */
.assistant-message .message-bubble {
  background-color: #18181b;
  color: #f4f4f5;
  border: 1px solid #27272a;
  border-bottom-left-radius: 3px;
}

.message-timestamp {
  font-size: 0.66rem;
  color: #71717a;
  margin-top: 1px;
}

.user-message .message-timestamp {
  text-align: right;
}

/* WELCOME BOX */
.welcome-box {
  max-width: 100%;
}

.welcome-box .message-body {
  background: #18181b;
  border: 1px solid #27272a;
  border-radius: 10px;
  padding: 14px;
  font-size: 0.85rem;
  line-height: 1.5;
  color: #d4d4d8;
}

.greeting-heading {
  margin: 0 0 5px;
  color: #ffffff;
}

.starter-chips {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #27272a;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.chips-label {
  font-size: 0.72rem;
  color: #a1a1aa;
  font-weight: 600;
}

.chip-btn {
  text-align: left;
  background: #222226;
  border: 1px solid #33333a;
  color: #ffffff;
  padding: 6px 11px;
  border-radius: 6px;
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.chip-btn:hover {
  background: #2c2c33;
  border-color: #52525b;
}

/* CITATIONS & CONTEXT (LIGHT SHADE OF BLACK) */
.citations-container {
  margin-top: 4px;
  background: #1a1a1e;
  border: 1px solid #27272a;
  border-radius: 8px;
  padding: 7px 11px;
  font-size: 0.76rem;
}

.citations-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  gap: 8px;
  flex-wrap: wrap;
}

.source-pill {
  background: #27272c;
  color: #ffffff;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  border: 1px solid #383840;
}

.toggle-link {
  color: #a1a1aa;
  font-size: 0.7rem;
}

.toggle-link:hover {
  color: #ffffff;
}

.context-drawer {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #27272a;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.context-chunk {
  background: #222226;
  border: 1px solid #2e2e34;
  border-radius: 6px;
  padding: 8px;
}

.chunk-badge {
  font-size: 0.66rem;
  color: #a1a1aa;
  font-weight: 700;
  margin-bottom: 4px;
  text-transform: uppercase;
}

.chunk-text {
  margin: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  color: #d4d4d8;
  white-space: pre-wrap;
  word-break: break-word;
}

/* LOADING TYPING INDICATOR */
.loading-bubble {
  display: flex;
  align-items: center;
  gap: 12px;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
}

.typing-indicator span {
  width: 5px;
  height: 5px;
  background-color: #a1a1aa;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.typing-label {
  font-size: 0.78rem;
  color: #a1a1aa;
}

/* CHAT INPUT BAR */
.chat-input-bar {
  padding: 12px 16px;
  background-color: #18181b;
  border-top: 1px solid #27272a;
  display: flex;
  align-items: flex-end;
  gap: 10px;
  flex-shrink: 0;
}

.question-input {
  flex: 1;
  background-color: #121214;
  border: 1px solid #2e2e34;
  border-radius: 8px;
  color: #ffffff;
  padding: 10px 13px;
  font-size: 0.86rem;
  font-family: inherit;
  resize: none;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.15s ease;
}

.question-input:focus {
  border-color: #52525b;
  box-shadow: 0 0 0 1px #52525b;
}

.send-btn {
  width: 42px;
  height: 42px;
  background: #ffffff;
  border: none;
  border-radius: 8px;
  color: #000000;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: #e4e4e7;
}

.send-btn:disabled {
  background: #27272a;
  color: #52525b;
  cursor: not-allowed;
}

/* SPINNER */
.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(0, 0, 0, 0.25);
  border-radius: 50%;
  border-top-color: #000000;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* RESPONSIVE STACKING FOR SMALLER SCREENS */
@media (max-width: 900px) {
  .app-layout {
    height: auto;
    min-height: 100vh;
    overflow-y: auto;
  }

  .workspace-grid {
    grid-template-columns: 1fr;
    height: auto;
    overflow: visible;
  }

  .preview-container {
    min-height: 420px;
  }

  .chat-pane {
    height: 600px;
  }
}
</style>
