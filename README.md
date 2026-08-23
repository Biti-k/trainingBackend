# Strength Trainer — Backend

The API behind [trainingFront](https://github.com/Biti-k/trainingFront): a FastAPI service for tracking strength-training workouts, exercises, and progress, with Google OAuth login and an AI training assistant on top of Google Gemini.

## Features

- **Google OAuth 2.0 login** — verifies the ID token server-side and issues a signed session JWT; no passwords stored.
- **Exercises & workouts** — full CRUD, scoped per user (every query filters by the authenticated user's ID, so one account can never read or modify another's data).
- **Exercise catalog** — a seeded reference table of common exercises (muscle group, equipment, instructions, images) that users can pull from instead of creating exercises from scratch.
- **Analytics** — workout summary, volume-by-exercise over time, progression stats, bodyweight trend, and per-exercise strength metrics.
- **AI assistant** (Gemini) — free-form chat, an automatic progress analysis, and a next-workout suggestion, each built from the user's actual last 30 days of training data. Rate-limited to 8 requests/hour per user across all three endpoints to keep API cost predictable.

## Tech stack

- [FastAPI](https://fastapi.tiangolo.com/) + [SQLAlchemy](https://www.sqlalchemy.org/) + [Alembic](https://alembic.sqlalchemy.org/) migrations
- PostgreSQL
- [PyJWT](https://pyjwt.readthedocs.io/) for session tokens, `google-auth` for OAuth
- [Google Gemini](https://ai.google.dev/) (`google-genai`) for the AI assistant

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate      # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

cp .env.example .env           # then fill in the values, see below
alembic upgrade head           # create/update the database schema

uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000` by default, with interactive docs at `/docs`. You'll also want the [frontend](https://github.com/Biti-k/trainingFront) running to actually use it end-to-end — the API alone has no UI beyond the Swagger docs.

### Environment variables

See [`.env.example`](.env.example) for the full list — a Postgres connection string, Google OAuth client credentials, a `SESSION_SECRET` for signing JWTs, a Gemini API key, and the frontend origin (for CORS and post-login redirects). None of these are optional; the app won't start without them.

### Seeding the exercise catalog

```bash
python scripts/seed_exercise_catalog.py
```

Loads `data/exercises_catalog.json` into the `exercise_catalog` table.

## Architecture notes

- **Auth flow**: `/auth/google/login` redirects to Google; `/auth/google/callback` verifies the returned ID token, upserts the user, and issues a session JWT (30-day expiry). Rather than putting that JWT directly in the redirect URL back to the frontend (where it would sit in browser history and access logs), the callback hands back a short-lived, single-use exchange code via `/auth/finish?code=...`; the frontend swaps it server-side for the real token through `POST /auth/exchange`. Every other endpoint requires a `Bearer <jwt>` header, verified in [`app/dependencies.py`](app/dependencies.py).
- **Data isolation**: every model with user-owned data carries a `user_id` foreign key, and every router filters by `current_user.id` — see [`app/routers/workouts.py`](app/routers/workouts.py) for the pattern, including cross-checking that referenced exercises belong to the same user.
- **AI context**: [`app/routers/ai.py`](app/routers/ai.py) builds a plain-text summary of the user's last 30 days of workouts and passes it to Gemini as context on every request — the model never sees other users' data.
