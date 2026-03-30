# Defines the POST /upload endpoint. Accepts a syllabus PDF uploaded by the
# user, passes it through the data pipeline (load → chunk → embed), and stores
# the resulting vectors in ChromaDB under a unique collection so they can be
# queried alongside the pre-ingested university policy documents.
