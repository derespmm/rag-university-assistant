# Loads and extracts text from PDF files. Uses pdfplumber as the primary
# parser (better handling of tables and multi-column layouts) with pypdf as
# a fallback. Returns raw text on a per-page basis so the chunker can
# preserve page-level metadata.
