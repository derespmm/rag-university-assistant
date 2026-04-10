# Defines the POST /upload endpoint. Accepts a syllabus PDF uploaded by the
# user, passes it through the data pipeline (load → chunk → embed), and stores
# the resulting vectors in ChromaDB under a unique collection so they can be
# queried alongside the pre-ingested university policy documents.

import os
import uuid
import tempfile
from pathlib import Path

import chromadb
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from backend.core.embedder import embed_chunks
from backend.data.chunker import chunk_pages
from backend.data.pdf_loader import load_pdf

router = APIRouter()

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")


class UploadResponse(BaseModel):
    collection_name: str
    filename: str
    chunks_ingested: int


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload a syllabus PDF and ingest it into a new ChromaDB collection.

    Returns a `collection_name` that the client should pass to `POST /chat`
    to query the uploaded syllabus alongside university policies.

    - Accepts only PDF files.
    - Each upload gets a unique collection name (UUID-based) so multiple
      syllabi can be stored independently without collisions.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF files are accepted.")

    # read uploaded bytes into a temp file so pdf_loader can open it by path
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        pages = load_pdf(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    if not pages:
        raise HTTPException(status_code=422, detail="Could not extract text from the uploaded PDF.")

    chunks = chunk_pages(pages)
    if not chunks:
        raise HTTPException(status_code=422, detail="PDF produced no text chunks after processing.")

    # give every chunk the original filename as its source so citations are readable
    for chunk in chunks:
        chunk["source"] = file.filename

    ids, embeddings, metadatas = embed_chunks(chunks)
    texts = [c["text"] for c in chunks]

    # each upload gets its own collection so syllabi don't pollute each other
    collection_name = f"syllabus_{uuid.uuid4().hex}"

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    collection.add(
        ids=ids,
        embeddings=embeddings,  # type: ignore[arg-type]
        documents=texts,
        metadatas=metadatas,  # type: ignore[arg-type]
    )

    return UploadResponse(
        collection_name=collection_name,
        filename=file.filename,
        chunks_ingested=len(chunks),
    )
