from services import dataset_search


def test_exact_match_is_labeled_original(monkeypatch):
    def fake_search(name, limit):
        return [{"name": "CIFAR-10", "repository": "Hugging Face Datasets", "doi": None,
                  "url": "https://huggingface.co/datasets/cifar10", "description": "desc"}]

    monkeypatch.setattr(dataset_search, "SOURCES", [("Hugging Face Datasets", fake_search)])
    result = dataset_search.search_dataset("CIFAR-10")
    assert result.kind == "original"
    assert result.status == "available"
    assert result.relevance_reason is None


def test_weak_match_is_labeled_alternative(monkeypatch):
    def fake_search(name, limit):
        return [{"name": "Fashion-MNIST", "repository": "Zenodo", "doi": "10.1234/x",
                  "url": "https://zenodo.org/record/1", "description": "desc"}]

    monkeypatch.setattr(dataset_search, "SOURCES", [("Zenodo", fake_search)])
    result = dataset_search.search_dataset("SomeCompletelyDifferentDatasetName2024")
    assert result.kind == "alternative"
    assert result.relevance_reason is not None
    assert "not confirmed" in result.relevance_reason


def test_no_results_is_not_found(monkeypatch):
    def fake_search(name, limit):
        return []

    monkeypatch.setattr(dataset_search, "SOURCES", [("Zenodo", fake_search)])
    result = dataset_search.search_dataset("NonexistentDatasetXYZ")
    assert result.kind == "not_found"
    assert result.status == "unavailable"


def test_one_source_failing_does_not_break_others(monkeypatch):
    def broken_search(name, limit):
        raise RuntimeError("network down")

    def working_search(name, limit):
        return [{"name": name, "repository": "UCI", "doi": None, "url": "https://x", "description": "d"}]

    monkeypatch.setattr(dataset_search, "SOURCES", [("Broken", broken_search), ("UCI", working_search)])
    result = dataset_search.search_dataset("SomeDataset")
    assert result.kind == "original"
