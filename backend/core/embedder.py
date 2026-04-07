# Wraps the OpenAI embeddings API. Provides a single function that takes a
# list of text chunks and returns their vector embeddings. Used by both the
# ingestion script (for policy docs) and the upload endpoint (for syllabi).

import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# The embedding model is configurable via .env so it can be swapped without
# touching code. text-embedding-3-small is fast and cheap; upgrade to
# text-embedding-3-large if retrieval accuracy needs improvement.
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def get_embedder() -> OpenAIEmbeddings:
    """
    Return a LangChain OpenAIEmbeddings instance.

    LangChain's OpenAIEmbeddings handles batching automatically — if you pass
    thousands of chunks it splits them into batches of 2048 and retries on
    rate limit errors, so callers don't need to manage that themselves.

    The instance reads OPENAI_API_KEY from the environment (loaded above via
    dotenv), so no key needs to be passed explicitly.
    """
    return OpenAIEmbeddings(model=EMBEDDING_MODEL)


def embed_chunks(chunks: list[dict]) -> tuple[list[str], list[list[float]], list[dict]]:
    """
    Embed a list of chunk dicts (from chunker.py) using the OpenAI API.

    Returns three parallel lists ready to insert directly into ChromaDB:
        - ids:        unique string ID for each chunk ("source__chunk_index")
        - embeddings: list of float vectors, one per chunk
        - metadatas:  list of metadata dicts (source, page, chunk index)

    ChromaDB's .add() method expects exactly these three lists plus the
    documents themselves, which callers can get from [c["text"] for c in chunks].

    Separating the three return values keeps this function focused on
    embedding and lets the caller (ingest_policies.py, upload.py) decide
    how to store the results.
    """
    embedder = get_embedder()

    texts = [c["text"] for c in chunks]

    # embed_documents() sends texts to the API and returns a list of vectors
    # in the same order as the input — order is guaranteed by LangChain
    embeddings = embedder.embed_documents(texts)

    ids = [f"{c['source']}__{c['chunk']}" for c in chunks]

    metadatas = [
        {
            "source": c["source"],
            "page": c["page"],
            "chunk": c["chunk"],
        }
        for c in chunks
    ]

    return ids, embeddings, metadatas
