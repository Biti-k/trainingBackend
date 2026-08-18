from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, exercises, workouts, analytics, ai, exercise_catalog

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Strength Trainer API",
    description="Backend API for tracking strength training workouts, exercises, and progress",
    version="1.0.0",
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4321")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(exercises.router)
app.include_router(workouts.router)
app.include_router(analytics.router)
app.include_router(ai.router)
app.include_router(exercise_catalog.router)

@app.get("/")
def root():
    return {"message": "Strength Trainer API", "docs": "/docs"}
