from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from typing import Optional

router = APIRouter(prefix="/exercise-catalog", tags=["exercise-catalog"])


@router.get("/", response_model=list[schemas.ExerciseCatalogItem])
def list_catalog(
    search: Optional[str] = None,
    muscle_group: Optional[str] = None,
    category: Optional[str] = None,
    equipment: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(models.ExerciseCatalog)
    if search:
        query = query.filter(models.ExerciseCatalog.name.ilike(f"%{search}%"))
    if muscle_group:
        query = query.filter(
            (models.ExerciseCatalog.muscle_group.ilike(f"%{muscle_group}%"))
            | (models.ExerciseCatalog.primary_muscles.ilike(f"%{muscle_group}%"))
        )
    if category:
        query = query.filter(models.ExerciseCatalog.category == category)
    if equipment:
        query = query.filter(models.ExerciseCatalog.equipment == equipment)
    return query.order_by(models.ExerciseCatalog.name).offset(skip).limit(limit).all()


@router.get("/{catalog_id}", response_model=schemas.ExerciseCatalogItem)
def get_catalog_item(catalog_id: int, db: Session = Depends(get_db)):
    item = db.query(models.ExerciseCatalog).filter(models.ExerciseCatalog.id == catalog_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Catalog exercise not found")
    return item
