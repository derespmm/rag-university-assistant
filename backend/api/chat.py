# Defines the POST /chat endpoint. Accepts a user question (and optionally a
# session/collection ID for a previously uploaded syllabus), runs it through
# the RAG pipeline, and returns the generated answer along with the source
# chunks that were retrieved.
