# Splits extracted PDF text into overlapping chunks suitable for embedding.
# Uses tiktoken to count tokens and respect the embedding model's context
# window. Attaches source metadata (filename, page number) to each chunk so
# retrieved results can be cited in the final answer.
