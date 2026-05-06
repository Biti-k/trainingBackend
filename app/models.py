from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workouts = relationship("Workout", back_populates="profile", cascade="all, delete-orphan")
    exercises = relationship("Exercise", back_populates="profile", cascade="all, delete-orphan")


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    muscle_group = Column(String, nullable=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)

    __table_args__ = (UniqueConstraint('name', 'profile_id', name='unique_exercise_name_per_profile'),)

    profile = relationship("Profile", back_populates="exercises")
    sets = relationship("Set", back_populates="exercise")


class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    bodyweight = Column(Float, nullable=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)

    profile = relationship("Profile", back_populates="workouts")
    sets = relationship("Set", back_populates="workout", cascade="all, delete-orphan")


class Set(Base):
    __tablename__ = "sets"

    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False, index=True)
    weight = Column(Float, nullable=False)
    reps = Column(Integer, nullable=False)
    rpe = Column(Float, nullable=True)
    order = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)

    workout = relationship("Workout", back_populates="sets")
    exercise = relationship("Exercise", back_populates="sets")
