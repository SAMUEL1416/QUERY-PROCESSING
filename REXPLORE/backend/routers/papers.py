"""
Endpoints for paper upload, listing, detail retrieval, raw file download,
and multi-paper comparison. All endpoints require authentication and are
scoped to the authenticated user - a user can only see/act on their own
papers.
"""
import os
import uuid
import logging

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.config import get_settings
from app.database import get_db
from services import pdf_processor, pipeline_service, comparison_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/papers", tags=["papers"])


def _safe_filename(original: str) -> str:
    ext = os.path.splitext(original)[1].lower() or ".pdf"
    return f"{uuid.uuid4().hex}{ext}"


@router.post("/upload", response_model=schemas.PaperOut, status_code=201)
async def upload_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    settings = get_settings()

    if file.content_type not in ("application/pdf", "application/x-pdf") and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds the {settings.max_upload_mb}MB limit.")

    try:
        pdf_processor.validate_pdf(contents)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    stored_filename = _safe_filename(file.filename)
    file_path = os.path.join(settings.upload_dir, stored_filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    paper = models.Paper(
        user_id=current_user.id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=file_path,
        status="uploading",
        status_detail="Uploading",
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    background_tasks.add_task(pipeline_service.run_pipeline, paper.id)

    return paper


@router.get("", response_model=list[schemas.PaperOut])
def list_papers(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return (
        db.query(models.Paper)
        .filter(models.Paper.user_id == current_user.id)
        .order_by(models.Paper.uploaded_at.desc())
        .all()
    )


@router.get("/{paper_id}", response_model=schemas.PaperDetailOut)
def get_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    paper = (
        db.query(models.Paper)
        .filter(models.Paper.id == paper_id, models.Paper.user_id == current_user.id)
        .first()
    )
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    return paper


@router.get("/{paper_id}/file")
def get_paper_file(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    paper = (
        db.query(models.Paper)
        .filter(models.Paper.id == paper_id, models.Paper.user_id == current_user.id)
        .first()
    )
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    if not os.path.exists(paper.file_path):
        raise HTTPException(status_code=404, detail="Stored file is missing on disk.")
    return FileResponse(paper.file_path, media_type="application/pdf", filename=paper.original_filename)


@router.post("/compare")
def compare_papers(
    payload: schemas.ComparisonRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    rows = comparison_service.compare_papers(db, payload.paper_ids, current_user.id)
    return {"comparison": rows}
