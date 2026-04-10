# Entry point for the FastAPI application. Creates the app instance, mounts
# the chat and upload routers, and configures CORS so the frontend can
# communicate with the backend during local development.

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.chat import router as chat_router
from backend.api.upload import router as upload_router

load_dotenv()

app = FastAPI(
    title="RAG University Assistant",
    description="Ask questions about university policies and course syllabi.",
    version="0.1.0",
)

# allow the Vite dev server (and any localhost origin) to call the API
FRONTEND_URL = os.getenv("VITE_API_BASE_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(upload_router)


@app.get("/health")
def health() -> dict:
    """Simple liveness check."""
    return {"status": "ok"}
