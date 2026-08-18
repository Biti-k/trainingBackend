import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, engine, Base
from app import models

DATA_FILE = Path(__file__).parent.parent / "data" / "exercises_catalog.json"
IMAGE_BASE = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"


def build_image_url(rel_path: str) -> str:
    return IMAGE_BASE + rel_path


def map_record(raw: dict) -> dict:
    images = raw.get("images") or []
    primary = raw.get("primaryMuscles") or []
    secondary = raw.get("secondaryMuscles") or []
    return {
        "external_id": raw["id"],
        "name": raw["name"],
        "muscle_group": primary[0].title() if primary else None,
        "primary_muscles": ",".join(primary) or None,
        "secondary_muscles": ",".join(secondary) or None,
        "category": raw.get("category"),
        "equipment": raw.get("equipment"),
        "level": raw.get("level"),
        "mechanic": raw.get("mechanic"),
        "force": raw.get("force"),
        "instructions": "\n".join(raw.get("instructions") or []) or None,
        "image_url": build_image_url(images[0]) if len(images) > 0 else None,
        "image_url_2": build_image_url(images[1]) if len(images) > 1 else None,
    }


def seed():
    Base.metadata.create_all(bind=engine)

    with open(DATA_FILE, encoding="utf-8") as f:
        raw_exercises = json.load(f)

    db = SessionLocal()
    try:
        for raw in raw_exercises:
            mapped = map_record(raw)
            existing = db.query(models.ExerciseCatalog).filter(
                models.ExerciseCatalog.external_id == mapped["external_id"]
            ).first()
            if existing:
                for k, v in mapped.items():
                    setattr(existing, k, v)
            else:
                db.add(models.ExerciseCatalog(**mapped))
        db.commit()
        count = db.query(models.ExerciseCatalog).count()
        print(f"Seed complete. exercise_catalog now has {count} rows.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
