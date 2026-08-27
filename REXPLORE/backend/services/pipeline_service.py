"""
Orchestrates the full MODULE 1 + dataset-detection pipeline that runs after
a PDF is uploaded:

  Reading Paper -> Detecting Sections -> Extracting Features ->
  Understanding Research -> Detecting Datasets -> Building Semantic Index -> Ready

Runs as a FastAPI BackgroundTask so the upload endpoint can return
immediately with status="uploading" and the frontend can poll
GET /api/papers/{id} for live status_detail updates.
"""
import logging
import traceback

from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from services import (
    pdf_processor,
    ocr_service,
    section_extractor,
    feature_extractor,
    research_understanding,
    embedding_service,
    dataset_detector,
    dataset_search,
)

logger = logging.getLogger(__name__)


def _set_status(db: Session, paper: models.Paper, status: str, detail: str):
    paper.status = status
    paper.status_detail = detail
    db.add(paper)
    db.commit()


def run_pipeline(paper_id: int):
    db = SessionLocal()
    try:
        paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
        if not paper:
            logger.error("Pipeline invoked for missing paper_id=%s", paper_id)
            return

        # ---- Reading Paper ----
        _set_status(db, paper, "processing", "Reading Paper")
        extraction = pdf_processor.extract_text(paper.file_path)
        paper.page_count = extraction.page_count

        # OCR fallback for pages with negligible extractable text
        pages = extraction.pages
        if any(p.needs_ocr for p in pages) and ocr_service.is_ocr_available():
            _set_status(db, paper, "processing", "Running OCR on scanned pages")
            for p in pages:
                if p.needs_ocr:
                    ocr_text = ocr_service.ocr_page(paper.file_path, p.page_number)
                    if ocr_text:
                        p.text = ocr_text
                        paper.used_ocr = True

        full_text = "\n\n".join(p.text for p in pages if p.text)

        if not full_text.strip():
            _set_status(db, paper, "error", "No extractable text found")
            paper.error_message = (
                "No readable text could be extracted from this PDF, even after OCR. "
                "The file may be corrupted, empty, or OCR is not installed on this server."
            )
            db.commit()
            return

        # ---- Detecting Sections ----
        _set_status(db, paper, "processing", "Detecting Sections")
        detected_sections = section_extractor.detect_sections(pages)

        # ---- Extracting Features ----
        _set_status(db, paper, "processing", "Extracting Features")
        features = feature_extractor.extract_all_features(full_text, pages)
        for feat in features:
            db.add(models.PaperFeature(
                paper_id=paper.id,
                feature_type=feat.feature_type,
                value=feat.value,
                context=feat.context,
                page_number=feat.page_number,
                confidence=feat.confidence,
            ))
        db.commit()

        # ---- Understanding Research ----
        _set_status(db, paper, "processing", "Understanding Research")
        global_concepts = [f.value.lower() for f in features if f.feature_type == "concept"]
        section_understandings = research_understanding.build_section_understanding(
            detected_sections, global_concepts
        )
        for su in section_understandings:
            db.add(models.PaperSection(
                paper_id=paper.id,
                name=su.name,
                page_number=su.page_number,
                order_index=su.order_index,
                raw_text=su.raw_text,
                key_points=su.key_points,
                simple_explanation=su.simple_explanation,
                concepts=su.concepts,
                findings=su.findings,
            ))
        db.commit()

        algorithm_names = [f.value for f in features if f.feature_type == "algorithm"]
        paper.research_domain = research_understanding.infer_research_domain(
            full_text, algorithm_names, global_concepts
        )

        # Try to infer a title from the first non-empty line of page 1 (never fabricated).
        if pages and pages[0].text:
            first_line = next((l.strip() for l in pages[0].text.split("\n") if len(l.strip()) > 8), None)
            if first_line and len(first_line) < 200:
                paper.title = first_line

        db.commit()

        # ---- Detecting Datasets ----
        _set_status(db, paper, "processing", "Detecting Datasets")
        dataset_names = dataset_detector.detect_dataset_names(full_text, pages)
        for name in dataset_names[:10]:  # cap to avoid excessive external calls on huge papers
            try:
                result = dataset_search.search_dataset(name)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Dataset search failed for %r: %s", name, exc)
                result = dataset_search.DatasetSearchResult(kind="not_found", status="unavailable")

            db.add(models.Dataset(
                paper_id=paper.id,
                mentioned_name=name,
                kind=result.kind,
                status=result.status,
                name=result.name,
                repository=result.repository,
                doi=result.doi,
                url=result.url,
                description=result.description,
                relevance_reason=result.relevance_reason,
                searched_at=__import__("datetime").datetime.utcnow(),
            ))
        db.commit()

        # ---- Building Semantic Index ----
        _set_status(db, paper, "processing", "Building Semantic Index")
        try:
            db_sections = db.query(models.PaperSection).filter(models.PaperSection.paper_id == paper.id).all()
            chunks = embedding_service.build_chunks_from_sections(db_sections)
            embedding_service.build_and_save_index(paper.id, chunks)
        except embedding_service.EmbeddingUnavailable as exc:
            logger.warning("Semantic index unavailable for paper %s: %s (keyword fallback will be used)", paper.id, exc)

        # ---- Ready ----
        import datetime as dt
        paper.processed_at = dt.datetime.utcnow()
        _set_status(db, paper, "ready", "Ready")

    except Exception as exc:  # noqa: BLE001
        logger.error("Pipeline failed for paper %s: %s\n%s", paper_id, exc, traceback.format_exc())
        db.rollback()
        paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
        if paper:
            paper.status = "error"
            paper.status_detail = "Processing failed"
            paper.error_message = "An internal error occurred while processing this paper."
            db.commit()
    finally:
        db.close()
