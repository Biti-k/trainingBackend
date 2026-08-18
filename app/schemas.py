from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ExerciseBase(BaseModel):
    name: str
    muscle_group: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class ExerciseCreate(ExerciseBase):
    pass


class Exercise(ExerciseBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExerciseCatalogItem(BaseModel):
    id: int
    external_id: str
    name: str
    muscle_group: Optional[str] = None
    primary_muscles: Optional[str] = None
    secondary_muscles: Optional[str] = None
    category: Optional[str] = None
    equipment: Optional[str] = None
    level: Optional[str] = None
    mechanic: Optional[str] = None
    force: Optional[str] = None
    instructions: Optional[str] = None
    image_url: Optional[str] = None
    image_url_2: Optional[str] = None

    class Config:
        from_attributes = True


class SetBase(BaseModel):
    exercise_id: int
    weight: float
    reps: int
    rpe: Optional[float] = None
    order: int = 0
    notes: Optional[str] = None


class SetCreate(SetBase):
    pass


class Set(SetBase):
    id: int
    workout_id: int

    class Config:
        from_attributes = True


class WorkoutBase(BaseModel):
    date: Optional[datetime] = None
    notes: Optional[str] = None
    bodyweight: Optional[float] = None


class WorkoutCreate(WorkoutBase):
    sets: list[SetCreate]


class Workout(WorkoutBase):
    id: int
    sets: list[Set] = []

    class Config:
        from_attributes = True


class VolumeByDate(BaseModel):
    date: datetime
    exercise_name: str
    total_volume: float
    total_reps: int
    max_weight: float


class ProgressionStats(BaseModel):
    exercise_name: str
    sessions: int
    max_weight: float
    max_weight_date: Optional[datetime] = None
    max_reps: int
    max_rpe: Optional[float] = None
    avg_weight: float
    volume_trend: list[float]
    estimated_1rm: Optional[float] = None


class WorkoutSummary(BaseModel):
    total_workouts: int
    total_volume: float
    avg_bodyweight: Optional[float] = None
    exercises_count: int
    date_range: tuple[str, str]

class User(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None

    class Config:
        from_attributes = True
