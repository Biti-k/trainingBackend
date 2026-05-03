import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from app import models
from datetime import datetime, timedelta
from typing import Optional


def get_workout_summary(db: Session) -> dict:
    workouts = db.query(models.Workout).all()
    if not workouts:
        return {
            "total_workouts": 0,
            "total_volume": 0.0,
            "avg_bodyweight": None,
            "exercises_count": 0,
            "date_range": ["", ""],
        }

    sets = db.query(models.Set).all()
    df = pd.DataFrame([
        {
            "weight": s.weight,
            "reps": s.reps,
            "exercise_id": s.exercise_id,
        }
        for s in sets
    ])

    total_volume = (df["weight"] * df["reps"]).sum() if len(df) else 0.0
    bodyweights = [w.bodyweight for w in workouts if w.bodyweight is not None]
    exercise_ids = df["exercise_id"].nunique() if len(df) else 0

    dates = sorted([w.date for w in workouts])
    return {
        "total_workouts": len(workouts),
        "total_volume": float(total_volume),
        "avg_bodyweight": float(np.mean(bodyweights)) if bodyweights else None,
        "exercises_count": exercise_ids,
        "date_range": [dates[0].isoformat(), dates[-1].isoformat()],
    }


def get_volume_by_exercise(
    db: Session, exercise_name: Optional[str] = None, days: int = 90
) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(days=days)

    query = (
        db.query(models.Set, models.Workout.date, models.Exercise.name)
        .join(models.Workout, models.Set.workout_id == models.Workout.id)
        .join(models.Exercise, models.Set.exercise_id == models.Exercise.id)
        .filter(models.Workout.date >= cutoff)
    )

    if exercise_name:
        query = query.filter(models.Exercise.name == exercise_name)

    rows = query.all()
    if not rows:
        return []

    data = [
        {
            "date": w,
            "exercise_name": e,
            "weight": s.weight,
            "reps": s.reps,
            "volume": s.weight * s.reps,
        }
        for s, w, e in rows
    ]
    df = pd.DataFrame(data)

    grouped = df.groupby(["date", "exercise_name"]).agg(
        total_volume=("volume", "sum"),
        total_reps=("reps", "sum"),
        max_weight=("weight", "max"),
    ).reset_index()

    return grouped.to_dict(orient="records")


def get_progression_stats(
    db: Session, exercise_name: Optional[str] = None
) -> list[dict]:
    query = (
        db.query(models.Set, models.Workout, models.Exercise)
        .join(models.Workout, models.Set.workout_id == models.Workout.id)
        .join(models.Exercise, models.Set.exercise_id == models.Exercise.id)
    )

    if exercise_name:
        query = query.filter(models.Exercise.name == exercise_name)

    rows = query.all()
    if not rows:
        return []

    data = [
        {
            "date": w.date,
            "exercise_name": e.name,
            "weight": s.weight,
            "reps": s.reps,
            "rpe": s.rpe,
        }
        for s, w, e in rows
    ]
    df = pd.DataFrame(data).sort_values("date")

    results = []
    for ex_name, group in df.groupby("exercise_name"):
        sessions = group["date"].nunique()
        max_weight = float(group["weight"].max())
        max_weight_idx = group["weight"].idxmax()
        max_weight_date = group.loc[max_weight_idx, "date"]
        max_reps = int(group.loc[max_weight_idx, "reps"])
        max_rpe = group.loc[max_weight_idx, "rpe"]
        avg_weight = float(np.mean(group["weight"]))

        volume_by_session = (
            group.assign(volume=group["weight"] * group["reps"])
            .groupby("date")["volume"]
            .sum()
            .tolist()
        )

        est_1rm = float(
            np.max(group["weight"] * (1 + group["reps"] / 30))
        ) if len(group) else None

        results.append({
            "exercise_name": ex_name,
            "sessions": sessions,
            "max_weight": max_weight,
            "max_weight_date": max_weight_date,
            "max_reps": max_reps,
            "max_rpe": max_rpe if pd.notna(max_rpe) else None,
            "avg_weight": round(avg_weight, 2),
            "volume_trend": volume_by_session,
            "estimated_1rm": round(est_1rm, 2) if est_1rm else None,
        })

    return results


def get_bodyweight_trend(db: Session, days: int = 90) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(days=days)

    workouts = (
        db.query(models.Workout)
        .filter(models.Workout.date >= cutoff)
        .filter(models.Workout.bodyweight.isnot(None))
        .order_by(models.Workout.date)
        .all()
    )

    if not workouts:
        return []

    df = pd.DataFrame([
        {"date": w.date, "bodyweight": w.bodyweight} for w in workouts
    ])

    df["sma_7"] = df["bodyweight"].rolling(window=7, min_periods=1).mean()

    return df.to_dict(orient="records")


def get_strength_metrics(db: Session, exercise_name: str) -> dict:
    query = (
        db.query(models.Set, models.Workout.date)
        .join(models.Workout, models.Set.workout_id == models.Workout.id)
        .join(models.Exercise, models.Set.exercise_id == models.Exercise.id)
        .filter(models.Exercise.name == exercise_name)
    )

    rows = query.all()
    if not rows:
        return {"error": "No data found"}

    data = [
        {
            "date": w,
            "weight": s.weight,
            "reps": s.reps,
            "rpe": s.rpe,
        }
        for s, w in rows
    ]
    df = pd.DataFrame(data).sort_values("date")
    df["est_1rm"] = df["weight"] * (1 + df["reps"] / 30)

    return {
        "exercise_name": exercise_name,
        "current_max": float(df["weight"].max()),
        "estimated_1rm_max": float(df["est_1rm"].max()),
        "avg_rpe": round(float(df["rpe"].mean()), 2) if df["rpe"].notna().any() else None,
        "total_sessions": int(df["date"].nunique()),
        "progression_rate": float(
            np.polyfit(range(len(df)), df["est_1rm"].tolist(), 1)[0]
        ) if len(df) > 1 else 0.0,
        "volume_by_week": (
            df.assign(volume=df["weight"] * df["reps"])
            .set_index("date")
            .resample("W")["volume"]
            .sum()
            .dropna()
            .tolist()
        ),
    }
