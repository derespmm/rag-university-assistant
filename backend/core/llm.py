# Handles communication with the OpenAI chat completions API. Defines the
# system prompt and the context-injection template, then sends the assembled
# prompt to the LLM and returns the response text.

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

SYSTEM_PROMPT = """You are a helpful university assistant. You answer questions \
about university policies and course syllabi based strictly on the provided context.

If the answer is not contained in the context, say so honestly — do not make up \
information or draw on outside knowledge. When possible, cite the source document \
and page number."""


def ask(question: str, context_chunks: list[dict]) -> str:
    """
    Send the question and retrieved context to the LLM and return the answer.

    Args:
        question:       The user's question.
        context_chunks: List of chunk dicts returned by retriever.retrieve().
                        Each dict must have 'text', 'source', and 'page' keys.

    Returns:
        The LLM's answer as a plain string.
    """
    context_block = _build_context(context_chunks)

    user_message = f"""Use the following context to answer the question.

--- CONTEXT ---
{context_block}
--- END CONTEXT ---

Question: {question}"""

    client = OpenAI()
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content or ""


def _build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block for the prompt."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source", "unknown")
        page = chunk.get("page", "?")
        text = chunk.get("text", "")
        parts.append(f"[{i}] (source: {source}, page: {page})\n{text}")
    return "\n\n".join(parts)
