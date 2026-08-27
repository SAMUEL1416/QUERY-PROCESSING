"""
Shared pytest fixtures. Builds a small real PDF on the fly with PyMuPDF
(no external test fixtures needed) so tests exercise the actual extraction
code path rather than mocked text.
"""
import os
import sys
import tempfile

import fitz
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


SAMPLE_SECTIONS = {
    "Abstract": "This paper studies a convolutional neural network approach for image classification. "
                "We evaluate accuracy and precision on the CIFAR-10 dataset.",
    "Introduction": "Image classification is a fundamental task in computer vision. "
                     "Prior systems relied on hand-crafted features before deep learning became dominant.",
    "Methodology": "We propose a CNN architecture trained with the Adam optimizer. "
                    "The model uses three convolutional layers followed by two dense layers.",
    "Results": "Our results show that the proposed CNN achieves 92 percent accuracy and an F1-Score of 0.90 "
                "on the CIFAR-10 benchmark, outperforming the baseline Random Forest model.",
    "Limitations": "The model was only evaluated on a single dataset and may not generalize to other domains.",
    "Conclusion": "We conclude that CNN-based methods are effective for this task and warrant further study.",
    "Future Work": "Future work will explore transformer-based architectures and additional datasets.",
}


@pytest.fixture(scope="session")
def sample_pdf_path():
    doc = fitz.open()
    for heading, body in SAMPLE_SECTIONS.items():
        page = doc.new_page()
        text = f"{heading}\n\n{body}"
        page.insert_text((72, 72), text, fontsize=11)

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    doc.save(tmp.name)
    doc.close()
    yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture()
def test_db(tmp_path, monkeypatch):
    """Provides an isolated SQLite DB per test."""
    db_path = tmp_path / "test_rexplore.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from app.config import get_settings
    get_settings.cache_clear()

    from app.database import Base, engine, SessionLocal
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
