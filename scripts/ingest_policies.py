# One-time (or on-update) script to ingest university policy PDFs into
# ChromaDB. Reads all PDFs from data/policies/, runs them through the
# pdf_loader and chunker, embeds the chunks, and persists them to the
# "policies" collection in the local vector store.
#
# Usage:
#   python scripts/ingest_policies.py
#
# Re-run any time the policy PDFs change (e.g. after re-scraping).
# The script is resumable — it checks which PDFs are already in ChromaDB
# and skips them, so interrupted runs can be continued without re-embedding
# documents that were already processed.
#
# To force a full rebuild from scratch, pass --rebuild:
#   python scripts/ingest_policies.py --rebuild

import os
import sys
from pathlib import Path

# allow imports from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chromadb
from dotenv import load_dotenv
from tqdm import tqdm

from backend.core.embedder import embed_chunks
from backend.data.chunker import chunk_pages
from backend.data.pdf_loader import load_pdf

load_dotenv()

POLICIES_DIR = Path("data/policies")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
COLLECTION_NAME = "policies"


def main() -> None:
    rebuild = "--rebuild" in sys.argv

    # --- find all policy PDFs ---
    pdf_files = sorted(POLICIES_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {POLICIES_DIR}. Run scripts/scrape_policies.py first.")
        return
    print(f"Found {len(pdf_files)} policy PDFs.")

    # --- connect to ChromaDB ---
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    if rebuild and COLLECTION_NAME in [c.name for c in client.list_collections()]:
        print(f"--rebuild flag set. Deleting existing '{COLLECTION_NAME}' collection...")
        client.delete_collection(COLLECTION_NAME)

    # get_or_create_collection is idempotent — safe to call on every run
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # build a set of source filenames already in ChromaDB so we can skip them
    # get() with no arguments returns all stored metadata
    existing = collection.get(include=["metadatas"])
    already_ingested: set[str] = set()
    if existing["metadatas"]:
        for meta in existing["metadatas"]:
            if meta and "source" in meta:
                already_ingested.add(str(meta["source"]))

    skipped = len(already_ingested)
    if skipped:
        print(f"Resuming — {skipped} source(s) already ingested, skipping them.")

    # --- process each PDF ---
    total_chunks = 0
    newly_ingested = 0

    for pdf_path in tqdm(pdf_files, desc="Ingesting PDFs"):
        if pdf_path.name in already_ingested:
            continue

        pages = load_pdf(pdf_path)
        if not pages:
            continue

        chunks = chunk_pages(pages)
        if not chunks:
            continue

        ids, embeddings, metadatas = embed_chunks(chunks)
        texts = [c["text"] for c in chunks]

        collection.add(
            ids=ids,
            embeddings=embeddings,  # type: ignore[arg-type]
            documents=texts,
            metadatas=metadatas,  # type: ignore[arg-type]
        )

        total_chunks += len(chunks)
        newly_ingested += 1

    print(f"\nDone. {total_chunks} new chunks from {newly_ingested} PDF(s) added to '{COLLECTION_NAME}'.")
    print(f"Vector store saved to {CHROMA_PATH}/")


if __name__ == "__main__":
    main()
