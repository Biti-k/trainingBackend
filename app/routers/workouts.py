from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.dependencies import get_current_user
from app import models, schemas
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/workouts", tags=["workouts"])


def _assert_owned_exercises(db: Session, user_id: int, exercise_ids: set[int]):
    if not exercise_ids:
        return
    owned = {
        row[0] for row in db.query(models.Exercise.id).filter(
            models.Exercise.id.in_(exercise_ids), models.Exercise.user_id == user_id,
        ).all()
    }
    missing = exercise_ids - owned
    if missing:
        raise HTTPException(status_code=400, detail=f"Exercises not found or not yours: {sorted(missing)}")


@router.get("/", response_model=list[schemas.Workout])
def list_workouts(
    skip: int = 0,
    limit: int = 50,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Workout).options(joinedload(models.Workout.sets)).filter(models.Workout.user_id == current_user.id)
    if start_date:
        query = query.filter(models.Workout.date >= start_date)
    if end_date:
        query = query.filter(models.Workout.date <= end_date)
    return query.order_by(models.Workout.date.desc()).offset(skip).limit(limit).all()


@router.get("/{workout_id}", response_model=schemas.Workout)
def get_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    workout = (
        db.query(models.Workout)
        .options(joinedload(models.Workout.sets))
        .filter(
            models.Workout.id == workout_id,
            models.Workout.user_id == current_user.id
        )
        .first()
    )
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@router.post("/", response_model=schemas.Workout, status_code=201)
def create_workout(
    workout: schemas.WorkoutCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _assert_owned_exercises(db, current_user.id, {s.exercise_id for s in workout.sets})

    db_workout = models.Workout(
        date=workout.date or datetime.utcnow(),
        notes=workout.notes,
        bodyweight=workout.bodyweight,
        user_id=current_user.id,
    )
    db.add(db_workout)
    db.flush()

    for set_data in workout.sets:
        db_set = models.Set(
            workout_id=db_workout.id,
            exercise_id=set_data.exercise_id,
            weight=set_data.weight,
            reps=set_data.reps,
            rpe=set_data.rpe,
            order=set_data.order,
            notes=set_data.notes,
        )
        db.add(db_set)

    db.commit()
    db.refresh(db_workout)
    return (
        db.query(models.Workout)
        .options(joinedload(models.Workout.sets))
        .filter(models.Workout.id == db_workout.id)
        .first()
    )


@router.put("/{workout_id}", response_model=schemas.Workout)
def update_workout(
    workout_id: int,
    workout_update: schemas.WorkoutCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    workout = db.query(models.Workout).filter(
        models.Workout.id == workout_id,
        models.Workout.user_id == current_user.id
    ).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    _assert_owned_exercises(db, current_user.id, {s.exercise_id for s in workout_update.sets})

    workout.date = workout_update.date or workout.date
    workout.notes = workout_update.notes
    workout.bodyweight = workout_update.bodyweight

    db.query(models.Set).filter(models.Set.workout_id == workout_id).delete()

    for set_data in workout_update.sets:
        db_set = models.Set(
            workout_id=workout_id,
            exercise_id=set_data.exercise_id,
            weight=set_data.weight,
            reps=set_data.reps,
            rpe=set_data.rpe,
            order=set_data.order,
            notes=set_data.notes,
        )
        db.add(db_set)

    db.commit()
    db.refresh(workout)
    return (
        db.query(models.Workout)
        .options(joinedload(models.Workout.sets))
        .filter(models.Workout.id == workout_id)
        .first()
    )


@router.delete("/{workout_id}", status_code=204)
def delete_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    workout = db.query(models.Workout).options(joinedload(models.Workout.sets)).filter(
        models.Workout.id == workout_id,
        models.Workout.user_id == current_user.id
    ).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    db.delete(workout)
    db.commit()
