# Handles communication with the OpenAI chat completions API. Defines the
# system prompt and the context-injection template, then sends the assembled
# prompt to the LLM and returns the response text.

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

SYSTEM_PROMPT = """You are a knowledgeable and precise university assistant. \
You answer questions about university policies and course syllabi using only \
the provided context.

Guidelines:
- Be thorough and specific. Quote or closely paraphrase the relevant policy text.
- List specific examples, consequences, or procedures when they appear in the context.
- If multiple sources are relevant, synthesize them into a complete answer.
- Cite each source by name and page number at the end of your answer.
- If the context does not contain enough information to answer fully, say so \
clearly rather than guessing."""


def ask(question: str, context_chunks: list[dict]) -> str:
    """
    Send the question and retrieved context to the LLM and return the answer.

    Args:
        question:       The user's original question.
        context_chunks: List of chunk dicts returned by retriever.retrieve().
                        Each dict must have 'text', 'source', and 'page' keys.

    Returns:
        The LLM's answer as a plain string.
    """
    context_block = _build_context(context_chunks)

    user_message = f"""Use the following context to answer the question as thoroughly \
as possible. List specific examples, procedures, and consequences where they appear. \
Do not summarize vaguely — quote or closely paraphrase the relevant details directly \
from the context.

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
        temperature=0.1,
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


def rewrite_query(question: str) -> str:
    """
    Use the LLM to rewrite the user's question into a more effective
    search query before hitting ChromaDB.

    The rewritten query is optimised for semantic similarity search:
    concise, keyword-rich, and free of conversational filler.

    Args:
        question: The raw user question.

    Returns:
        A rewritten query string.
    """
    client = OpenAI()
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a search query optimiser. Rewrite the user's question "
                    "into a concise, keyword-rich search query that will retrieve the "
                    "most relevant university policy or syllabus text from a vector "
                    "database. Output only the rewritten query — no explanation."
                ),
            },
            {"role": "user", "content": question},
        ],
        temperature=0.0,
    )
    return response.choices[0].message.content or question
