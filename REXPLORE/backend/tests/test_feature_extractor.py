from services import pdf_processor, feature_extractor


def test_extracts_known_algorithm(sample_pdf_path):
    extraction = pdf_processor.extract_text(sample_pdf_path)
    features = feature_extractor.extract_algorithms(extraction.full_text, extraction.pages)
    values = [f.value for f in features]
    assert "Convolutional Neural Network" in values or "CNN" in values
    assert "Random Forest" in values


def test_extracts_known_metrics(sample_pdf_path):
    extraction = pdf_processor.extract_text(sample_pdf_path)
    features = feature_extractor.extract_metrics(extraction.full_text, extraction.pages)
    values = [f.value for f in features]
    assert "Accuracy" in values
    assert "F1-Score" in values


def test_extracts_dataset_mentions(sample_pdf_path):
    extraction = pdf_processor.extract_text(sample_pdf_path)
    features = feature_extractor.extract_dataset_mentions(extraction.full_text, extraction.pages)
    values = [f.value for f in features]
    assert any("CIFAR" in v for v in values)


def test_concepts_are_stopword_filtered(sample_pdf_path):
    extraction = pdf_processor.extract_text(sample_pdf_path)
    features = feature_extractor.extract_concepts_keywords(extraction.full_text, extraction.pages)
    values = [f.value.lower() for f in features]
    assert "the" not in values
    assert "with" not in values
