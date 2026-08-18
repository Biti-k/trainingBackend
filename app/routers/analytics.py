from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.services import analytics
from app import models
from typing import Optional

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return analytics.get_workout_summary(db, current_user.id)


@router.get("/volume")
def get_volume_by_exercise(
    exercise_name: Optional[str] = None,
    days: int = Query(default=90, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return analytics.get_volume_by_exercise(db, current_user.id, exercise_name, days)


@router.get("/progression")
def get_progression(
    exercise_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return analytics.get_progression_stats(db, current_user.id, exercise_name)


@router.get("/bodyweight")
def get_bodyweight_trend(
    days: int = Query(default=90, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return analytics.get_bodyweight_trend(db, current_user.id, days)


@router.get("/strength/{exercise_name}")
def get_strength_metrics(
    exercise_name: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return analytics.get_strength_metrics(db, current_user.id, exercise_name)
