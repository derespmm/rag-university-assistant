# RAG University Assistant

A chatbot that lets students ask questions about university policies and upload a course syllabus to query alongside those policies. Built with FastAPI, ChromaDB, and the OpenAI API.

---

## How it works

The app uses an advanced RAG (Retrieval-Augmented Generation) pipeline:

1. **Hybrid search** — combines vector similarity search with BM25 keyword search and merges results via Reciprocal Rank Fusion (RRF). Vector search finds semantically similar chunks; BM25 catches exact policy terms like "suspension" or "fine".
2. **Context window expansion** — after retrieving a chunk, the chunks immediately before and after it are fetched and stitched in, giving the LLM full surrounding context.
3. **Generation** — the top-k expanded chunks are injected into a prompt and sent to the LLM, which produces a grounded answer with source citations.

---

## Project structure

```
rag-university-assistant/
├── backend/
│   ├── api/              # route handlers (chat.py, upload.py)
│   ├── core/             # RAG pipeline (embedder, retriever, llm, pipeline)
│   ├── data/             # PDF parsing and chunking
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx       # chat UI and syllabus upload form
│       ├── main.jsx      # React entry point
│       ├── App.css
│       └── index.css
├── data/
│   ├── policies/         # university policy PDFs (gitignored)
│   ├── syllabi/          # sample syllabi for testing (gitignored)
│   └── sample_queries/
├── scripts/
│   ├── setup.sh          # one-time dev environment setup
│   └── ingest_policies.py
└── tests/                # manual test scripts
```

---

## Getting started (do this once)

### 1. Install system requirements

Before running the setup script, make sure you have the following installed:

- **Python 3.12** — https://python.org (3.12.x specifically — 3.13+ breaks several dependencies that require pre-built wheels)
- **Node.js 22 (LTS)** — https://nodejs.org
- **Git** — https://git-scm.com

On Windows, also install **Git Bash** (it comes bundled with Git for Windows). All terminal commands in this README should be run from Git Bash, not Command Prompt or PowerShell.

### 2. Clone the repo

```bash
git clone https://github.com/derespmm/rag-university-assistant.git
cd rag-university-assistant
```

### 3. Create the virtual environment and install dependencies

Create the venv using Python 3.12 explicitly:

```bash
py -3.12 -m venv .venv
```

Activate it. In Git Bash:
```bash
source .venv/Scripts/activate
```

In PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies using `uv` (much faster than plain pip):

```bash
pip install uv
uv pip install -r backend/requirements.txt
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Add your OpenAI API key

Copy `.env.example` to `.env` and fill in your key:

```bash
cp .env.example .env
```

```
OPENAI_API_KEY=sk-...
```

Get a key at https://platform.openai.com/api-keys. Never share this key or commit it to git — the `.env` file is gitignored.

### 6. Ingest university policy documents

Place policy PDFs in `data/policies/`, then run:

```bash
python scripts/ingest_policies.py
```

This embeds the documents and stores them in the local ChromaDB vector store. You only need to re-run this if the policy documents change.

### 7. Start the app

In one terminal (backend):
```bash
source .venv/Scripts/activate
uvicorn backend.main:app --reload
```

In a second terminal (frontend):
```bash
cd frontend
npm run dev
```

Then open `http://localhost:5173` in your browser.

---

## Daily workflow

### Every time you open a new terminal

The virtual environment doesn't stay active between sessions. Reactivate it each time:

```bash
source .venv/Scripts/activate
```

Your prompt will show `(.venv)` when it's active.

### Before starting any work

Sync with main before you start coding to avoid merge conflicts later:

```bash
git checkout main
git pull
git checkout your-branch
git merge main
```

### Never code directly on main

All work happens on a feature branch. Create one before you start:

```bash
git checkout -b feature/your-feature-name
```

### Committing your work

```bash
git status                        # always check what you're about to stage
git add .
git commit -m "describe what and why, not just what"
git push origin your-branch-name
```

Then open a pull request on GitHub to merge into main.

### If you install a new Python package

Update `requirements.txt` immediately and commit it:

```bash
uv pip install some-package
uv pip freeze > backend/requirements.txt
git add backend/requirements.txt
git commit -m "add some-package to requirements"
```

### Running tests

Test scripts live in `tests/` and can be run directly:

```bash
python tests/test_pipeline.py
python tests/test_retriever.py
python tests/test_llm.py
```

---

## Things not to do

- **Don't commit `.env`** — it contains your API key. It's gitignored, but stay aware of it.
- **Don't commit PDFs** — the `data/` directory is gitignored. Policy documents can be large and may be sensitive.
- **Don't `git add .` without checking `git status` first** — it's easy to accidentally stage files you didn't mean to.
- **Don't push directly to main** — always go through a branch and pull request.
- **Don't install packages outside the virtual environment** — if `(.venv)` isn't showing in your prompt, reactivate before installing anything.
