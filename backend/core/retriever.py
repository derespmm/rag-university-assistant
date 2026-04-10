# Wraps ChromaDB similarity search. Given a query string, embeds it and
# returns the top-k most relevant document chunks from the vector store.
# Supports querying both the university policy collection and a
# per-upload syllabus collection.

import os

import chromadb
from dotenv import load_dotenv

from backend.core.embedder import get_embedder

load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
POLICIES_COLLECTION = "policies"


def retrieve(
    query: str,
    *,
    collection_name: str = POLICIES_COLLECTION,
    top_k: int = 5,
) -> list[dict]:
    """
    Embed the query and return the top-k most similar chunks from ChromaDB.

    Each returned dict has:
        - text:     the chunk text (document)
        - source:   filename the chunk came from
        - page:     page number within that file
        - chunk:    chunk index within that page
        - distance: cosine distance (lower = more similar)

    Args:
        query:           The user's question.
        collection_name: Which ChromaDB collection to search. Defaults to the
                         pre-ingested university policy collection. Pass a
                         per-upload collection name to search a syllabus instead.
        top_k:           Number of chunks to return.
    """
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(collection_name)

    embedder = get_embedder()
    query_vector = embedder.embed_query(query)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks: list[dict] = []
    docs = results["documents"][0]  # type: ignore[index]
    metas = results["metadatas"][0]  # type: ignore[index]
    distances = results["distances"][0]  # type: ignore[index]

    for doc, meta, dist in zip(docs, metas, distances):
        chunks.append(
            {
                "text": doc,
                "source": meta.get("source", ""),
                "page": meta.get("page", 0),
                "chunk": meta.get("chunk", 0),
                "distance": dist,
            }
        )

    return chunks
