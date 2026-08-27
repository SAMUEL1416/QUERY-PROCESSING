"""
Endpoint for MODULE 2 query processing: ask a paper-grounded question and
get back an extractive answer plus page/section sources. Scoped to the
authenticated user's own papers.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db
from services import query_processor

router = APIRouter(prefix="/api/queries", tags=["queries"])


def _get_owned_paper(db: Session, paper_id: int, user_id: int) -> models.Paper:
    paper = (
        db.query(models.Paper)
        .filter(models.Paper.id == paper_id, models.Paper.user_id == user_id)
        .first()
    )
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    return paper


@router.post("", response_model=schemas.QueryAnswerOut)
def ask_question(
    payload: schemas.QueryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    paper = _get_owned_paper(db, payload.paper_id, current_user.id)
    if paper.status != "ready":
        raise HTTPException(status_code=409, detail=f"Paper is not ready yet (status: {paper.status}).")

    result = query_processor.process_query(paper.id, payload.question, paper.sections)

    query_row = models.QueryHistory(
        paper_id=paper.id,
        query_text=payload.question,
        answer_text=result.answer,
        retrieval_method=result.retrieval_method,
    )
    db.add(query_row)
    db.commit()
    db.refresh(query_row)

    for src in result.sources:
        db.add(models.QuerySource(
            query_id=query_row.id,
            section_name=src.section_name,
            page_number=src.page_number,
            snippet=src.snippet,
            score=src.score,
        ))
    db.commit()
    db.refresh(query_row)

    return query_row


@router.get("/paper/{paper_id}", response_model=list[schemas.QueryAnswerOut])
def get_query_history(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _get_owned_paper(db, paper_id, current_user.id)
    return (
        db.query(models.QueryHistory)
        .filter(models.QueryHistory.paper_id == paper_id)
        .order_by(models.QueryHistory.created_at.desc())
        .all()
    )
