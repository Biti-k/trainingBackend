from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app import models, schemas
from typing import Optional

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("/", response_model=list[schemas.Exercise])
def list_exercises(
    muscle_group: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Exercise).filter(models.Exercise.user_id == current_user.id)
    if muscle_group:
        query = query.filter(models.Exercise.muscle_group.ilike(f"%{muscle_group}%"))
    return query.order_by(models.Exercise.name).offset(skip).limit(limit).all()


@router.get("/{exercise_id}", response_model=schemas.Exercise)
def get_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    exercise = db.query(models.Exercise).filter(
        models.Exercise.id == exercise_id,
        models.Exercise.user_id == current_user.id
    ).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise


@router.post("/", response_model=schemas.Exercise, status_code=201)
def create_exercise(
    exercise: schemas.ExerciseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_exercise = models.Exercise(**exercise.model_dump(), user_id=current_user.id)
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)
    return db_exercise


@router.post("/from-catalog/{catalog_id}", response_model=schemas.Exercise, status_code=201)
def create_exercise_from_catalog(
    catalog_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    catalog_item = db.query(models.ExerciseCatalog).filter(models.ExerciseCatalog.id == catalog_id).first()
    if not catalog_item:
        raise HTTPException(status_code=404, detail="Catalog exercise not found")

    existing = db.query(models.Exercise).filter(
        models.Exercise.user_id == current_user.id,
        models.Exercise.name == catalog_item.name,
    ).first()
    if existing:
        return existing

    db_exercise = models.Exercise(
        name=catalog_item.name,
        muscle_group=catalog_item.muscle_group,
        description=catalog_item.instructions,
        image_url=catalog_item.image_url,
        user_id=current_user.id,
    )
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)
    return db_exercise


@router.put("/{exercise_id}", response_model=schemas.Exercise)
def update_exercise(
    exercise_id: int,
    exercise_update: schemas.ExerciseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    exercise = db.query(models.Exercise).filter(
        models.Exercise.id == exercise_id,
        models.Exercise.user_id == current_user.id
    ).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    for key, value in exercise_update.model_dump().items():
        setattr(exercise, key, value)
    db.commit()
    db.refresh(exercise)
    return exercise


@router.delete("/{exercise_id}", status_code=204)
def delete_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    exercise = db.query(models.Exercise).filter(
        models.Exercise.id == exercise_id,
        models.Exercise.user_id == current_user.id
    ).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    db.delete(exercise)
    db.commit()
