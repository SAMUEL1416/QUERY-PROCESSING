"""Research Analytics endpoints - real backend-derived counters and charts,
scoped to the authenticated user's own data."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db
from services import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview", response_model=schemas.AnalyticsOverviewOut)
def overview(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return analytics_service.get_overview(db, current_user.id)


@router.get("/features", response_model=schemas.AnalyticsFeaturesOut)
def features(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return analytics_service.get_feature_distributions(db, current_user.id)
