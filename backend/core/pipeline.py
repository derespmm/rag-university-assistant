# Orchestrates the full RAG query flow. Given a user question, it calls the
# retriever to fetch relevant chunks from ChromaDB, injects them into a prompt
# as context, then calls the LLM to generate a grounded answer. This is the
# central module that chat.py calls.
#
# Advanced RAG pipeline:
#   1. Retrieval — hybrid BM25 + vector search merged via Reciprocal Rank Fusion
#   2. Expansion — each retrieved chunk is expanded with neighboring chunks
#   3. Generation — LLM answers using the expanded top-k chunks as context

from backend.core.llm import ask
from backend.core.retriever import retrieve

POLICIES_COLLECTION = "policies"


def run(
    question: str,
    *,
    collection_name: str = POLICIES_COLLECTION,
    top_k: int = 5,
) -> dict:
    """
    Run the full advanced RAG pipeline for a user question.

    Args:
        question:        The user's question.
        collection_name: ChromaDB collection to retrieve from. Defaults to the
                         pre-ingested policy collection. Pass a per-upload
                         collection name to query a syllabus instead.
        top_k:           Number of chunks to pass to the LLM after merging.

    Returns:
        A dict with:
            - answer:  The LLM-generated answer string.
            - sources: List of source dicts (source, page, chunk, rrf_score)
                       for the chunks used as context.
    """
    chunks = retrieve(question, collection_name=collection_name, top_k=top_k)

    answer = ask(question, chunks)

    sources = [
        {
            "source": c["source"],
            "page": c["page"],
            "chunk": c["chunk"],
            "rrf_score": c.get("rrf_score", 0.0),
        }
        for c in chunks
    ]

    return {"answer": answer, "sources": sources}
