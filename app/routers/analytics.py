from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import analytics
from app.routers.auth import get_current_user
from app import models
from typing import Optional

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def get_summary(profile_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verify profile belongs to user
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id, models.Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return analytics.get_workout_summary(db, profile_id)


@router.get("/volume")
def get_volume_by_exercise(
    profile_id: int,
    exercise_name: Optional[str] = None,
    days: int = Query(default=90, ge=1, le=365),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify profile belongs to user
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id, models.Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return analytics.get_volume_by_exercise(db, profile_id, exercise_name, days)


@router.get("/progression")
def get_progression(
    profile_id: int,
    exercise_name: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify profile belongs to user
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id, models.Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return analytics.get_progression_stats(db, profile_id, exercise_name)


@router.get("/bodyweight")
def get_bodyweight_trend(
    profile_id: int,
    days: int = Query(default=90, ge=1, le=365),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify profile belongs to user
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id, models.Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return analytics.get_bodyweight_trend(db, profile_id, days)


@router.get("/strength/{exercise_name}")
def get_strength_metrics(
    profile_id: int,
    exercise_name: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify profile belongs to user
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id, models.Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return analytics.get_strength_metrics(db, profile_id, exercise_name)
