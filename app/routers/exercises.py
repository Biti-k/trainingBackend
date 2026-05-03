from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from typing import Optional

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("/", response_model=list[schemas.Exercise])
def list_exercises(
    muscle_group: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(models.Exercise)
    if muscle_group:
        query = query.filter(models.Exercise.muscle_group.ilike(f"%{muscle_group}%"))
    return query.order_by(models.Exercise.name).offset(skip).limit(limit).all()


@router.get("/{exercise_id}", response_model=schemas.Exercise)
def get_exercise(exercise_id: int, db: Session = Depends(get_db)):
    exercise = db.query(models.Exercise).filter(models.Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise


@router.post("/", response_model=schemas.Exercise, status_code=201)
def create_exercise(exercise: schemas.ExerciseCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Exercise).filter(models.Exercise.name == exercise.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Exercise already exists")
    db_exercise = models.Exercise(**exercise.model_dump())
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)
    return db_exercise


@router.put("/{exercise_id}", response_model=schemas.Exercise)
def update_exercise(
    exercise_id: int, exercise_update: schemas.ExerciseCreate, db: Session = Depends(get_db)
):
    exercise = db.query(models.Exercise).filter(models.Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    for key, value in exercise_update.model_dump().items():
        setattr(exercise, key, value)
    db.commit()
    db.refresh(exercise)
    return exercise


@router.delete("/{exercise_id}", status_code=204)
def delete_exercise(exercise_id: int, db: Session = Depends(get_db)):
    exercise = db.query(models.Exercise).filter(models.Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    db.delete(exercise)
    db.commit()
