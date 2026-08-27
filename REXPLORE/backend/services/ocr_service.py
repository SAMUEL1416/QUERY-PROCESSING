"""
OCR fallback for scanned PDF pages (pages where PyMuPDF extracted ~no text).
Uses Tesseract via pytesseract. Requires the tesseract binary to be installed
on the host machine (e.g. `apt install tesseract-ocr` / `brew install tesseract`).
"""
import io
import logging

from app.config import get_settings
from services.pdf_processor import render_page_image

logger = logging.getLogger(__name__)


def _configure_tesseract():
    settings = get_settings()
    if settings.tesseract_cmd:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


def is_ocr_available() -> bool:
    try:
        import pytesseract
        _configure_tesseract()
        pytesseract.get_tesseract_version()
        return True
    except Exception:  # noqa: BLE001
        return False


def ocr_page(file_path: str, page_number: int) -> str:
    """
    Rasterizes the given page and runs Tesseract OCR on it.
    Returns an empty string (never fabricated text) if OCR is unavailable
    or fails.
    """
    try:
        import pytesseract
        from PIL import Image

        _configure_tesseract()
        png_bytes = render_page_image(file_path, page_number)
        image = Image.open(io.BytesIO(png_bytes))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("OCR failed for page %s: %s", page_number, exc)
        return ""
