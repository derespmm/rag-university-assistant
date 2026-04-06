# Splits extracted PDF text into overlapping chunks suitable for embedding.
# Uses tiktoken to count tokens and respect the embedding model's context
# window. Attaches source metadata (filename, page number) to each chunk so
# retrieved results can be cited in the final answer.

import tiktoken

# text-embedding-3-small (the model we use for embeddings) has an 8191 token
# limit per input. Chunks of 512 tokens with 50-token overlap are a common
# starting point — small enough that each chunk stays semantically focused,
# with enough overlap that sentences split across chunk boundaries aren't lost.
CHUNK_SIZE = 512    # max tokens per chunk
CHUNK_OVERLAP = 50  # tokens shared between consecutive chunks


def _get_encoder():
    # cl100k_base is the tokenizer used by all text-embedding-3-* and gpt-4
    # models. Using the real tokenizer (instead of splitting on word count)
    # means our chunk sizes are accurate for the model that will process them.
    return tiktoken.get_encoding("cl100k_base")


def chunk_pages(pages: list[dict], chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """
    Split a list of page dicts (from pdf_loader) into token-bounded chunks.

    Each returned chunk dict has:
        - "text":    the chunk's text content
        - "source":  filename, carried forward from the page dict
        - "page":    page number the chunk started on
        - "chunk":   0-based index of this chunk within its source document

    Strategy:
        1. Encode every page's text into token IDs using tiktoken.
        2. Slide a window of `chunk_size` tokens across the token stream,
           stepping forward by (chunk_size - overlap) each time.
        3. Decode each window back to a string and record its metadata.

    Working in token space (not character or word space) guarantees that no
    chunk exceeds the embedding model's context window regardless of how
    dense the text is.
    """
    enc = _get_encoder()
    chunks = []
    chunk_index = 0

    for page in pages:
        text = page["text"]
        if not text:
            # skip blank pages (scanned images, cover pages, etc.)
            continue

        # encode the full page text into a list of integer token IDs
        token_ids = enc.encode(text)

        step = chunk_size - overlap  # how far to advance the window each time
        start = 0

        while start < len(token_ids):
            end = start + chunk_size
            window = token_ids[start:end]

            # decode the token window back into a human-readable string
            chunk_text = enc.decode(window)

            chunks.append({
                "text": chunk_text,
                "source": page["source"],
                "page": page["page"],
                "chunk": chunk_index,
            })

            chunk_index += 1
            start += step

    return chunks
