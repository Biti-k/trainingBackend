from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/profiles", tags=["profiles"])

@router.get("/", response_model=list[schemas.Profile])
def list_profiles(db: Session = Depends(get_db)):
    return db.query(models.Profile).order_by(models.Profile.name).all()


@router.post("/", response_model=schemas.Profile, status_code=201)
def create_profile(profile: schemas.ProfileCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Profile).filter(models.Profile.name == profile.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")
    db_profile = models.Profile(**profile.model_dump())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


@router.delete("/{profile_id}", status_code=204)
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(profile)
    db.commit()