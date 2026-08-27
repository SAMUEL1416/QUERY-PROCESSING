"""
Extracts complete page-by-page text from a PDF using PyMuPDF (fitz).
Pages with negligible extractable text are flagged for OCR fallback.
"""
from dataclasses import dataclass
from typing import List

import fitz  # PyMuPDF


MIN_CHARS_PER_PAGE_BEFORE_OCR = 25  # below this, treat the page as "scanned"


@dataclass
class PageText:
    page_number: int  # 1-indexed
    text: str
    needs_ocr: bool


@dataclass
class PdfExtractionResult:
    page_count: int
    pages: List[PageText]
    full_text: str
    used_ocr: bool


def validate_pdf(file_bytes: bytes) -> None:
    """Raises ValueError if the bytes are not a valid, openable PDF."""
    if not file_bytes.startswith(b"%PDF"):
        raise ValueError("File does not appear to be a valid PDF (missing %PDF header).")
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if doc.page_count < 1:
            raise ValueError("PDF has no pages.")
        doc.close()
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not open PDF: {exc}") from exc


def extract_text(file_path: str) -> PdfExtractionResult:
    """
    Extracts text from every page. Pages with little/no extractable text
    (typical of scanned documents) are marked needs_ocr=True so the caller
    (research_understanding service) can invoke ocr_service on just those pages.
    """
    doc = fitz.open(file_path)
    pages: List[PageText] = []

    for i in range(doc.page_count):
        page = doc.load_page(i)
        text = page.get_text("text") or ""
        text = text.strip()
        pages.append(
            PageText(
                page_number=i + 1,
                text=text,
                needs_ocr=len(text) < MIN_CHARS_PER_PAGE_BEFORE_OCR,
            )
        )

    doc.close()

    full_text = "\n\n".join(p.text for p in pages if p.text)
    used_ocr = False  # set True later if ocr_service actually fills in pages

    return PdfExtractionResult(
        page_count=len(pages),
        pages=pages,
        full_text=full_text,
        used_ocr=used_ocr,
    )


def render_page_image(file_path: str, page_number: int, zoom: float = 2.0):
    """Rasterizes a single page (1-indexed) to a PIL-compatible PNG byte buffer, for OCR."""
    doc = fitz.open(file_path)
    try:
        page = doc.load_page(page_number - 1)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        return pix.tobytes("png")
    finally:
        doc.close()
