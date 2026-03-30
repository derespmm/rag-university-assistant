# One-time (or on-update) script to ingest university policy PDFs into
# ChromaDB. Reads all PDFs from data/policies/, runs them through the
# pdf_loader and chunker, embeds the chunks, and persists them to the
# "policies" collection in the local vector store.
