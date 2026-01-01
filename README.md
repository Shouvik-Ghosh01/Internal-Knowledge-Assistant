# 📘 Internal Knowledge Assistant (Agentic RAG)

An **Agent-based Retrieval Augmented Generation (RAG)** system designed to answer internal company questions using **grounded, document-backed responses only**.

This system is built to reduce onboarding time, standardize knowledge access, and prevent hallucinations by strictly answering from approved internal documents.

---

## 🚀 Features

* ✅ Agentic RAG architecture (single intelligent agent)
* ✅ Multi-document, multi-namespace vector retrieval
* ✅ Strict grounding (no external knowledge)
* ✅ Source attribution for every answer
* ✅ Safety & prompt-injection protection
* ✅ Deployed backend (FastAPI) + frontend (Streamlit)
* ✅ Cloud-hosted vector database (Pinecone)

---

## 🧠 Supported Knowledge Sources

| Document Type          | Format | Namespace    |
| ---------------------- | ------ | ------------ |
| PR Review Checklist    | DOCX   | `pr_review`  |
| SOP / Onboarding Guide | DOCX   | `sop`        |
| Validation Checklist   | XLSX   | `validation` |
| UI Locators & Keywords | XLSX   | `locators`   |

Each document type is ingested separately with **custom chunking logic** and stored in its own Pinecone namespace.

---

## 🏗️ Architecture Overview

* **Frontend**: Streamlit (user interaction)
* **Backend**: FastAPI (API & orchestration)
* **Agent**: ReAct-style controller (tool-aware)
* **Retriever**: Vector similarity search (Pinecone)
* **LLM**: OpenAI (answer generation only)
* **Safety**:

  * Input validation
  * Prompt injection detection
  * Output filtering
* **Storage**: Pinecone Vector Database

---

## 🔁 System Workflow

1. User submits a question via Streamlit UI
2. FastAPI receives the request
3. Input is validated for scope & safety
4. Agent decides whether retrieval is required
5. Retriever embeds the query and searches Pinecone
6. Relevant chunks are returned (multi-namespace)
7. LLM generates answer **only using retrieved context**
8. Sources are extracted from retrieved metadata
9. Final safe response is returned to the UI

---

## 🛡️ Safety & Reliability

### Input Safety

* Blocks out-of-scope topics
* Detects prompt-injection patterns
* Enforces query length limits

### Output Safety

* Filters unsafe responses
* Returns fallback when context is insufficient
* Never fabricates information

### Hallucination Prevention

* LLM can only answer using retrieved chunks
* If no relevant context → `"I don't know based on the available knowledge base."`

---

## ⚙️ Setup & Run (Local)

### 1. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Fill in:

* `OPENAI_API_KEY`
* `PINECONE_API_KEY`
* `PINECONE_ENV`

---

### 4. Ingest documents

```bash
python scripts/ingest_all.py
```

---

### 5. Start backend

```bash
uvicorn backend.app:app --reload
```

---

### 6. Start frontend

```bash
streamlit run ui/streamlit_app.py
```

---

## ☁️ Deployment

* **Backend**: Render (FastAPI)
* **Frontend**: Streamlit Cloud
* **Secrets**: Managed via environment variables (never committed)

---

## 🧩 Design Rationale

* **Single Agent**: Simpler, faster, easier to reason about
* **Multi-namespace RAG**: Clear separation of document types
* **Agent over simple RAG**: Allows future routing, planning, and tool expansion
* **OpenAI embeddings (1536-d)**: Balanced quality vs cost
* **Pinecone**: Production-grade vector search

---

## 📌 Future Improvements

* Query routing agent (doc-type aware)
* Answer formatting per document type
* Caching for frequent queries
* Usage analytics & monitoring
* LLM provider fallback

---

> *This system demonstrates a production-grade, safety-aware implementation of Agentic RAG suitable for real-world enterprise use.*
