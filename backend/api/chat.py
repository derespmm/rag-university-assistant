# Defines the POST /chat endpoint. Accepts a user question (and optionally a
# session/collection ID for a previously uploaded syllabus), runs it through
# the RAG pipeline, and returns the generated answer along with the source
# chunks that were retrieved.

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.pipeline import run

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    collection_name: str = "policies"
    top_k: int = 5


class SourceItem(BaseModel):
    source: str
    page: int
    chunk: int
    rrf_score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Run a RAG query and return the LLM answer with source citations.

    - **question**: The user's natural-language question.
    - **collection_name**: ChromaDB collection to search. Defaults to "policies".
      Pass a per-upload collection name to query a syllabus instead.
    - **top_k**: Number of chunks to retrieve (default 5).
    """
    if not request.question.strip():
        raise HTTPException(status_code=422, detail="question must not be empty")

    try:
        result = run(
            request.question,
            collection_name=request.collection_name,
            top_k=request.top_k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(
        answer=result["answer"],
        sources=[SourceItem(**s) for s in result["sources"]],
    )
