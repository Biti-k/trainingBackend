from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import exercises, workouts, analytics, profiles

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Strength Trainer API",
    description="Backend API for tracking strength training workouts, exercises, and progress",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(exercises.router)
app.include_router(workouts.router)
app.include_router(analytics.router)
app.include_router(profiles.router)


@app.get("/")
def root():
    return {"message": "Strength Trainer API", "docs": "/docs"}
