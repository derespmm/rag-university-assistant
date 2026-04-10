# Wraps ChromaDB similarity search. Given a query string, embeds it and
# returns the top-k most relevant document chunks from the vector store.
# Supports querying both the university policy collection and a
# per-upload syllabus collection.
#
# Advanced RAG:
#   1. Hybrid search  — combines vector similarity with BM25 keyword search
#                       and merges results via Reciprocal Rank Fusion (RRF).
#                       Vector search finds semantically similar chunks;
#                       BM25 catches exact policy terms like "suspension" or
#                       "fine" that embeddings may gloss over.
#   2. Context window expansion — after retrieving a chunk, the chunks
#                       immediately before and after it (from the same source)
#                       are fetched and stitched in. This gives the LLM the
#                       full surrounding context rather than an isolated snippet.

import os
from collections import defaultdict

import chromadb
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi

from backend.core.embedder import get_embedder

load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
POLICIES_COLLECTION = "policies"

# How many candidates each search arm fetches before merging.
CANDIDATE_MULT = 3

# How many neighboring chunks to attach on each side during expansion.
CONTEXT_WINDOW = 1

# BM25 indexes are expensive to build — cache them per collection name.
_bm25_cache: dict[str, tuple[BM25Okapi, list[dict], dict]] = {}


def _build_bm25(collection) -> tuple[BM25Okapi, list[dict], dict]:
    """
    Build a BM25 index over every document in the collection.

    Also returns:
        all_chunks  — list of every chunk dict (text + metadata)
        chunk_map   — dict keyed by (source, chunk_idx) for fast neighbor lookup
    """
    name = collection.name
    if name in _bm25_cache:
        return _bm25_cache[name]

    results = collection.get(include=["documents", "metadatas"])
    docs: list[str] = results["documents"]  # type: ignore[assignment]
    metas: list[dict] = results["metadatas"]  # type: ignore[assignment]
    ids: list[str] = results["ids"]

    all_chunks = [
        {
            "id": id_,
            "text": doc,
            "source": meta.get("source", ""),
            "page": meta.get("page", 0),
            "chunk": meta.get("chunk", 0),
        }
        for id_, doc, meta in zip(ids, docs, metas)
    ]

    tokenized = [doc.lower().split() for doc in docs]
    bm25 = BM25Okapi(tokenized)

    # keyed by (source, chunk_index) so we can fetch neighbors in O(1)
    chunk_map = {(c["source"], c["chunk"]): c for c in all_chunks}

    _bm25_cache[name] = (bm25, all_chunks, chunk_map)
    return bm25, all_chunks, chunk_map


def _rrf_merge(
    vector_hits: list[dict],
    bm25_hits: list[dict],
    k: int = 60,
) -> list[dict]:
    """
    Merge two ranked lists with Reciprocal Rank Fusion.

    RRF score = 1/(k + rank) summed across both lists.
    A higher score means the chunk ranked well in both searches.
    """
    scores: dict[str, float] = defaultdict(float)
    id_to_chunk: dict[str, dict] = {}

    for rank, chunk in enumerate(vector_hits):
        id_ = chunk["id"]
        scores[id_] += 1 / (k + rank + 1)
        id_to_chunk[id_] = chunk

    for rank, chunk in enumerate(bm25_hits):
        id_ = chunk["id"]
        scores[id_] += 1 / (k + rank + 1)
        id_to_chunk[id_] = chunk

    sorted_ids = sorted(scores, key=lambda i: scores[i], reverse=True)
    merged = []
    for id_ in sorted_ids:
        chunk = dict(id_to_chunk[id_])
        chunk["rrf_score"] = scores[id_]
        merged.append(chunk)
    return merged


def _expand_context(chunk: dict, chunk_map: dict, window: int = CONTEXT_WINDOW) -> str:
    """
    Stitch neighboring chunks from the same source around the retrieved chunk.

    e.g. window=1 → prepend chunk[i-1] and append chunk[i+1] if they exist.
    """
    source = chunk["source"]
    idx = chunk["chunk"]

    parts = []
    for i in range(idx - window, idx + window + 1):
        neighbor = chunk_map.get((source, i))
        if neighbor:
            parts.append(neighbor["text"])

    return " ".join(parts)


def retrieve(
    query: str,
    *,
    collection_name: str = POLICIES_COLLECTION,
    top_k: int = 5,
) -> list[dict]:
    """
    Hybrid search: run vector search and BM25 in parallel, merge with RRF,
    then expand each result's context window before returning top_k chunks.

    Each returned dict has:
        - text:      expanded chunk text (chunk + neighbors)
        - source:    filename the chunk came from
        - page:      page number of the retrieved chunk
        - chunk:     chunk index of the retrieved chunk
        - distance:  cosine distance from vector search (0 if BM25-only hit)
        - rrf_score: merged relevance score from RRF (higher = more relevant)
    """
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(collection_name)

    bm25, all_chunks, chunk_map = _build_bm25(collection)

    n_candidates = min(top_k * CANDIDATE_MULT, len(all_chunks))

    # --- vector search arm ---
    embedder = get_embedder()
    query_vector = embedder.embed_query(query)

    vec_results = collection.query(
        query_embeddings=[query_vector],
        n_results=n_candidates,
        include=["documents", "metadatas", "distances"],
    )

    vec_hits: list[dict] = []
    for doc, meta, dist, id_ in zip(
        vec_results["documents"][0],  # type: ignore[index]
        vec_results["metadatas"][0],  # type: ignore[index]
        vec_results["distances"][0],  # type: ignore[index]
        vec_results["ids"][0],        # type: ignore[index]
    ):
        vec_hits.append(
            {
                "id": id_,
                "text": doc,
                "source": meta.get("source", ""),
                "page": meta.get("page", 0),
                "chunk": meta.get("chunk", 0),
                "distance": dist,
            }
        )

    # --- BM25 search arm ---
    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)

    # pair each chunk with its BM25 score and take the top candidates
    scored = sorted(
        zip(bm25_scores, all_chunks),
        key=lambda x: x[0],
        reverse=True,
    )
    bm25_hits = [chunk for _, chunk in scored[:n_candidates]]

    # add a placeholder distance for BM25-only hits
    for chunk in bm25_hits:
        chunk.setdefault("distance", 0.0)

    # --- merge with RRF ---
    merged = _rrf_merge(vec_hits, bm25_hits)[:top_k]

    # --- context window expansion ---
    for chunk in merged:
        chunk["text"] = _expand_context(chunk, chunk_map)

    return merged
