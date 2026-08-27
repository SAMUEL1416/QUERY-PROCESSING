"""
Aggregates real backend data (no mock numbers) for the Dashboard/Analytics
pages: overview counters and chart-ready distributions. All figures are
scoped to a single user's own papers.
"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models


def get_overview(db: Session, user_id: int) -> dict:
    own_papers = models.Paper.user_id == user_id

    papers_analyzed = (
        db.query(func.count(models.Paper.id))
        .filter(own_papers, models.Paper.status == "ready")
        .scalar() or 0
    )
    sections_extracted = (
        db.query(func.count(models.PaperSection.id))
        .join(models.Paper, models.PaperSection.paper_id == models.Paper.id)
        .filter(own_papers)
        .scalar() or 0
    )
    features_extracted = (
        db.query(func.count(models.PaperFeature.id))
        .join(models.Paper, models.PaperFeature.paper_id == models.Paper.id)
        .filter(own_papers)
        .scalar() or 0
    )
    datasets_discovered = (
        db.query(func.count(models.Dataset.id))
        .join(models.Paper, models.Dataset.paper_id == models.Paper.id)
        .filter(own_papers)
        .scalar() or 0
    )
    queries_processed = (
        db.query(func.count(models.QueryHistory.id))
        .join(models.Paper, models.QueryHistory.paper_id == models.Paper.id)
        .filter(own_papers)
        .scalar() or 0
    )

    algorithms_count = (
        db.query(func.count(models.PaperFeature.id))
        .join(models.Paper, models.PaperFeature.paper_id == models.Paper.id)
        .filter(own_papers, models.PaperFeature.feature_type == "algorithm")
        .scalar() or 0
    )
    metrics_count = (
        db.query(func.count(models.PaperFeature.id))
        .join(models.Paper, models.PaperFeature.paper_id == models.Paper.id)
        .filter(own_papers, models.PaperFeature.feature_type == "metric")
        .scalar() or 0
    )
    concepts_count = (
        db.query(func.count(models.PaperFeature.id))
        .join(models.Paper, models.PaperFeature.paper_id == models.Paper.id)
        .filter(own_papers, models.PaperFeature.feature_type == "concept")
        .scalar() or 0
    )

    return {
        "papers_analyzed": papers_analyzed,
        "datasets_discovered": datasets_discovered,
        "features_extracted": features_extracted,
        "queries_processed": queries_processed,
        "sections_extracted": sections_extracted,
        "algorithms_count": algorithms_count,
        "metrics_count": metrics_count,
        "concepts_count": concepts_count,
    }


def _top_distribution(db: Session, feature_type: str, user_id: int, limit: int = 10):
    rows = (
        db.query(models.PaperFeature.value, func.count(models.PaperFeature.id))
        .join(models.Paper, models.PaperFeature.paper_id == models.Paper.id)
        .filter(models.Paper.user_id == user_id, models.PaperFeature.feature_type == feature_type)
        .group_by(models.PaperFeature.value)
        .order_by(func.count(models.PaperFeature.id).desc())
        .limit(limit)
        .all()
    )
    return [{"label": label, "count": count} for label, count in rows]


def get_feature_distributions(db: Session, user_id: int) -> dict:
    algorithm_distribution = _top_distribution(db, "algorithm", user_id)
    metric_distribution = _top_distribution(db, "metric", user_id)
    concept_distribution = _top_distribution(db, "concept", user_id)

    dataset_rows = (
        db.query(models.Dataset.kind, func.count(models.Dataset.id))
        .join(models.Paper, models.Dataset.paper_id == models.Paper.id)
        .filter(models.Paper.user_id == user_id)
        .group_by(models.Dataset.kind)
        .all()
    )
    dataset_availability = [{"label": kind or "unresolved", "count": count} for kind, count in dataset_rows]

    return {
        "algorithm_distribution": algorithm_distribution,
        "metric_distribution": metric_distribution,
        "dataset_availability": dataset_availability,
        "concept_distribution": concept_distribution,
    }
