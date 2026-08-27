from services import pdf_processor, section_extractor


def test_detects_known_sections(sample_pdf_path):
    extraction = pdf_processor.extract_text(sample_pdf_path)
    sections = section_extractor.detect_sections(extraction.pages)
    names = [s.name for s in sections]

    for expected in ["Abstract", "Introduction", "Methodology", "Results", "Limitations", "Conclusion", "Future Work"]:
        assert expected in names


def test_section_text_is_not_empty_for_populated_sections(sample_pdf_path):
    extraction = pdf_processor.extract_text(sample_pdf_path)
    sections = section_extractor.detect_sections(extraction.pages)
    methodology = next(s for s in sections if s.name == "Methodology")
    assert "Adam optimizer" in methodology.raw_text


def test_no_headings_falls_back_to_full_text():
    from services.pdf_processor import PageText
    pages = [PageText(page_number=1, text="Just some plain unlabeled text with no headings.", needs_ocr=False)]
    sections = section_extractor.detect_sections(pages)
    assert len(sections) == 1
    assert sections[0].name == "Full Text"
