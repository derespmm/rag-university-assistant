# Orchestrates the full RAG query flow. Given a user question, it calls the
# retriever to fetch relevant chunks from ChromaDB, injects them into a prompt
# as context, then calls the LLM to generate a grounded answer. This is the
# central module that chat.py calls.
