# RAG University Assistant

A chatbot that lets students upload a course syllabus and ask questions that are answered using both the syllabus and official university policy documents. Built with LangChain, ChromaDB, and the OpenAI API.

---

## Project structure

```
rag-university-assistant/
├── backend/
│   ├── api/          # route handlers (chat, upload)
│   ├── core/         # RAG pipeline logic (embedder, retriever, llm)
│   ├── data/         # PDF parsing and chunking
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       └── utils/
├── data/
│   ├── policies/     # university policy PDFs (gitignored)
│   ├── syllabi/      # sample syllabi for testing (gitignored)
│   └── sample_queries/
├── scripts/
│   ├── setup.sh      # one-time dev environment setup
│   └── ingest_policies.py
└── docs/
```

---

## Getting started (do this once)

### 1. Install system requirements

Before running the setup script, make sure you have the following installed:

- **Python 3.10+** — https://python.org
- **Node.js 22 (LTS)** — https://nodejs.org
- **Git** — https://git-scm.com

On Windows, also install **Git Bash** (it comes bundled with Git for Windows). All terminal commands in this README should be run from Git Bash, not Command Prompt or PowerShell.

### 2. Clone the repo

```bash
git clone https://github.com/derespmm/rag-university-assistant.git
cd rag-university-assistant
```

### 3. Run the setup script

```bash
bash scripts/setup.sh
```

This will:
- Check that Python 3.10+ and Node 18+ are installed
- Copy `.env.example` to `.env`
- Create a Python virtual environment at `.venv/`
- Install all Python dependencies from `backend/requirements.txt`
- Install frontend Node dependencies (once `package.json` exists)
- Create any missing data directories
- Run a smoke test to confirm key packages imported correctly

### 4. Add your OpenAI API key

Open `.env` and fill in your key:

```
OPENAI_API_KEY=sk-...
```

Get a key at https://platform.openai.com/api-keys. Never share this key or commit it to git — the `.env` file is gitignored for this reason.

### 5. Ingest university policy documents

Place policy PDFs in `data/policies/`, then run:

```bash
python scripts/ingest_policies.py
```

This embeds the documents and stores them in the local ChromaDB vector store. You only need to re-run this if the policy documents change.

### 6. Start the app

In one terminal (backend):
```bash
source .venv/bin/activate
uvicorn backend.main:app --reload
```

In a second terminal (frontend):
```bash
cd frontend
npm run dev
```

---

## Daily workflow

### Every time you open a new terminal

The virtual environment doesn't stay active between sessions. You need to reactivate it each time:

```bash
source .venv/bin/activate
```

Your prompt will show `(.venv)` when it's active. All `pip install` and `python` commands should be run with the environment active.

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

Good branch names describe what you're building:
- `feature/pdf-ingestion`
- `feature/chat-api`
- `feature/frontend-upload`
- `feature/accuracy-eval`

### Committing your work

Save progress often — don't wait until a feature is complete to commit.

```bash
git status                        # always check what you're about to stage
git add .
git commit -m "describe what and why, not just what"
git push origin your-branch-name
```

Then open a pull request on GitHub to merge into main.

### If you install a new Python package

Update `requirements.txt` immediately and commit it so the other person gets it:

```bash
pip install some-package
pip freeze > backend/requirements.txt
git add backend/requirements.txt
git commit -m "add some-package to requirements"
```

### Running tests

```bash
pytest backend/tests/
```

---

## Things not to do

- **Don't commit `.env`** — it contains your API key. It's gitignored, but stay aware of it.
- **Don't commit PDFs** — the `data/` directory is gitignored. Policy documents can be large and may be sensitive.
- **Don't `git add .` without checking `git status` first** — it's easy to accidentally stage files you didn't mean to.
- **Don't push directly to main** — always go through a branch and pull request.
- **Don't install packages outside the virtual environment** — if `(.venv)` isn't showing in your prompt, reactivate before installing anything.