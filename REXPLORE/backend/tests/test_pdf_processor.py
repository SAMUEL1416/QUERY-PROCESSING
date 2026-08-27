import pytest

from services import pdf_processor


def test_validate_pdf_rejects_non_pdf_bytes():
    with pytest.raises(ValueError):
        pdf_processor.validate_pdf(b"not a pdf at all")


def test_validate_pdf_accepts_real_pdf(sample_pdf_path):
    with open(sample_pdf_path, "rb") as f:
        contents = f.read()
    pdf_processor.validate_pdf(contents)  # should not raise


def test_extract_text_returns_all_pages(sample_pdf_path):
    result = pdf_processor.extract_text(sample_pdf_path)
    assert result.page_count == 7  # one page per SAMPLE_SECTIONS entry
    assert len(result.pages) == 7
    assert "Abstract" in result.full_text
    assert "Methodology" in result.full_text


def test_pages_with_text_do_not_need_ocr(sample_pdf_path):
    result = pdf_processor.extract_text(sample_pdf_path)
    assert all(not p.needs_ocr for p in result.pages)
