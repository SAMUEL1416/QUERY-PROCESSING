import os

from services import synthetic_generator


def test_generates_csv_with_requested_columns(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "services.synthetic_generator.get_settings",
        lambda: type("S", (), {"generated_dir": str(tmp_path)})(),
    )
    columns = [
        {"name": "age", "type": "integer"},
        {"name": "score", "type": "float"},
        {"name": "label", "type": "category", "categories": ["yes", "no"]},
    ]
    result = synthetic_generator.generate_synthetic_csv(
        paper_id=1, dataset_id=1, row_count=20, columns=columns, seed=42
    )
    assert os.path.exists(result["file_path"])
    assert len(result["preview"]) == 10

    with open(result["file_path"]) as f:
        first_line = f.readline()
    assert "SYNTHETIC DATASET" in first_line


def test_same_seed_is_reproducible(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "services.synthetic_generator.get_settings",
        lambda: type("S", (), {"generated_dir": str(tmp_path)})(),
    )
    columns = [{"name": "value", "type": "integer"}]
    r1 = synthetic_generator.generate_synthetic_csv(1, 1, 5, columns, seed=7)
    r2 = synthetic_generator.generate_synthetic_csv(1, 2, 5, columns, seed=7)
    assert r1["preview"] == r2["preview"]


def test_unsupported_column_type_raises():
    import pytest
    with pytest.raises(ValueError):
        synthetic_generator._gen_column("unsupported_type", 5, __import__("numpy").random.default_rng(1))
