"""
Dataset Intelligence endpoints: list datasets detected for a paper, re-run
a live search for one dataset, and generate/download a synthetic CSV as a
last resort. All access is scoped to the authenticated user's own papers.
"""
import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db
from services import dataset_search, synthetic_generator

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


def _get_owned_paper(db: Session, paper_id: int, user_id: int) -> models.Paper:
    paper = (
        db.query(models.Paper)
        .filter(models.Paper.id == paper_id, models.Paper.user_id == user_id)
        .first()
    )
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    return paper


def _get_owned_dataset(db: Session, dataset_id: int, user_id: int) -> models.Dataset:
    dataset = (
        db.query(models.Dataset)
        .join(models.Paper, models.Dataset.paper_id == models.Paper.id)
        .filter(models.Dataset.id == dataset_id, models.Paper.user_id == user_id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return dataset


@router.get("/paper/{paper_id}", response_model=list[schemas.DatasetOut])
def get_datasets_for_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _get_owned_paper(db, paper_id, current_user.id)
    return db.query(models.Dataset).filter(models.Dataset.paper_id == paper_id).all()


@router.get("/{dataset_id}/search", response_model=schemas.DatasetOut)
def refresh_dataset_search(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Re-runs a live search across real repositories for this dataset mention."""
    dataset = _get_owned_dataset(db, dataset_id, current_user.id)

    result = dataset_search.search_dataset(dataset.mentioned_name)
    dataset.kind = result.kind
    dataset.status = result.status
    dataset.name = result.name
    dataset.repository = result.repository
    dataset.doi = result.doi
    dataset.url = result.url
    dataset.description = result.description
    dataset.relevance_reason = result.relevance_reason
    dataset.searched_at = dt.datetime.utcnow()
    db.commit()
    db.refresh(dataset)
    return dataset


@router.post("/{dataset_id}/synthetic", response_model=schemas.SyntheticDatasetOut)
def create_synthetic_dataset(
    dataset_id: int,
    payload: schemas.SyntheticDatasetCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    dataset = _get_owned_dataset(db, dataset_id, current_user.id)

    if dataset.kind in ("original", "alternative"):
        raise HTTPException(
            status_code=409,
            detail="A real dataset (original or alternative) is already available for this entry; "
                   "synthetic generation is only offered as a last resort.",
        )

    columns = [c.model_dump() for c in payload.columns]
    for col in columns:
        if col["type"] == "category" and not col.get("categories"):
            raise HTTPException(status_code=400, detail=f"Column '{col['name']}' of type 'category' needs a categories list.")

    try:
        gen = synthetic_generator.generate_synthetic_csv(
            paper_id=dataset.paper_id,
            dataset_id=dataset.id,
            row_count=payload.row_count,
            columns=columns,
            seed=payload.seed,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Failed to generate synthetic dataset.") from exc

    synthetic = models.SyntheticDataset(
        dataset_id=dataset.id,
        paper_id=dataset.paper_id,
        row_count=payload.row_count,
        columns=columns,
        seed=payload.seed,
        file_path=gen["file_path"],
    )
    db.add(synthetic)

    dataset.kind = "synthetic"
    dataset.status = "available"
    db.commit()
    db.refresh(synthetic)

    return schemas.SyntheticDatasetOut(
        id=synthetic.id,
        dataset_id=synthetic.dataset_id,
        row_count=synthetic.row_count,
        columns=synthetic.columns,
        seed=synthetic.seed,
        created_at=synthetic.created_at,
        preview=gen["preview"],
    )


@router.get("/synthetic/{synthetic_id}/download")
def download_synthetic_dataset(
    synthetic_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    synthetic = (
        db.query(models.SyntheticDataset)
        .join(models.Paper, models.SyntheticDataset.paper_id == models.Paper.id)
        .filter(models.SyntheticDataset.id == synthetic_id, models.Paper.user_id == current_user.id)
        .first()
    )
    if not synthetic:
        raise HTTPException(status_code=404, detail="Synthetic dataset not found.")
    return FileResponse(
        synthetic.file_path,
        media_type="text/csv",
        filename=f"synthetic_dataset_{synthetic_id}.csv",
    )
