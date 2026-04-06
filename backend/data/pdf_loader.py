# Loads and extracts text from PDF files. Uses pdfplumber as the primary
# parser (better handling of tables and multi-column layouts) with pypdf as
# a fallback. Returns raw text on a per-page basis so the chunker can
# preserve page-level metadata.

import pdfplumber
import pypdf
from pathlib import Path


def load_pdf(file_path: str | Path) -> list[dict]:
    """
    Extract text from a PDF file, one dict per page.

    Each returned dict has:
        - "page":     1-based page number
        - "text":     extracted text string for that page
        - "source":   the filename (no directory path), used later as citation metadata

    pdfplumber is tried first because it handles tables and multi-column
    layouts more accurately than pypdf. If pdfplumber fails for any reason
    (corrupt page, unusual encoding, etc.), pypdf is used as a fallback for
    that individual page rather than failing the whole document.
    """
    path = Path(file_path)
    source_name = path.name  # e.g. "academic_integrity_policy.pdf"
    pages = []

    # --- primary pass: pdfplumber ---
    # pdfplumber opens the PDF and gives us a list of Page objects.
    # page.extract_text() returns a plain string for that page, or None
    # if the page contains no extractable text (e.g. a scanned image page).
    try:
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages.append({
                    "page": i + 1,       # convert 0-based index to 1-based
                    "text": text.strip(),
                    "source": source_name,
                })
        return pages

    except Exception as primary_error:
        # pdfplumber failed on the whole file (e.g. encrypted or malformed PDF).
        # Fall through to the pypdf path below.
        print(f"[pdf_loader] pdfplumber failed on {source_name}: {primary_error}")
        print(f"[pdf_loader] retrying with pypdf fallback...")

    # --- fallback pass: pypdf ---
    # pypdf's PdfReader gives us a list of PageObject instances.
    # page.extract_text() is less sophisticated but handles most standard PDFs.
    pages = []
    with pypdf.PdfReader(path) as reader:
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages.append({
                "page": i + 1,
                "text": text.strip(),
                "source": source_name,
            })

    return pages


def load_pdfs_from_dir(dir_path: str | Path) -> list[dict]:
    """
    Load every PDF in a directory, returning all pages across all files
    as a single flat list.

    The "source" field on each page dict identifies which file it came from,
    so the chunker can carry that forward as citation metadata.
    """
    dir_path = Path(dir_path)
    all_pages = []

    pdf_files = sorted(dir_path.glob("*.pdf"))
    if not pdf_files:
        print(f"[pdf_loader] no PDF files found in {dir_path}")
        return all_pages

    for pdf_file in pdf_files:
        print(f"[pdf_loader] loading {pdf_file.name}...")
        pages = load_pdf(pdf_file)
        all_pages.extend(pages)

    print(f"[pdf_loader] loaded {len(pdf_files)} file(s), {len(all_pages)} page(s) total")
    return all_pages
