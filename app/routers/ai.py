from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from google import genai
from google.genai import types
import os

from app.database import get_db
from app import models

router = APIRouter(prefix="/ai", tags=["AI"])

# ── Configuración del cliente Gemini ──────────────────────────────────────────

_client = genai.Client(api_key=os.getenv("API_GEMINI"))

_SYSTEM_INSTRUCTION = (
    "Eres un asistente experto en fitness y entrenamiento de fuerza. "
    "Analizas datos reales de entrenos y das consejos prácticos, concisos y motivadores. "
    "Responde siempre en el mismo idioma que el usuario."
)

_CONFIG = types.GenerateContentConfig(
    system_instruction=_SYSTEM_INSTRUCTION,
)


# ── Schemas de request/response ───────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    profile_id: Optional[int] = None  # si se pasa, incluye contexto del perfil


class ChatResponse(BaseModel):
    reply: str


class AnalysisResponse(BaseModel):
    analysis: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_profile_context(profile_id: int, db: Session) -> str:
    """Construye un resumen textual del perfil para pasarlo como contexto a la IA."""

    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    # Últimos 30 días de entrenos
    since = datetime.utcnow() - timedelta(days=30)
    workouts = (
        db.query(models.Workout)
        .filter(
            models.Workout.profile_id == profile_id,
            models.Workout.date >= since,
        )
        .order_by(models.Workout.date.desc())
        .limit(10)
        .all()
    )

    if not workouts:
        return f"Perfil: {profile.name}. Sin entrenos registrados en los últimos 30 días."

    lines = [f"Perfil: {profile.name}"]
    lines.append(f"Entrenos recientes ({len(workouts)} en los últimos 30 días):")

    for w in workouts:
        date_str = w.date.strftime("%d/%m/%Y")
        sets_summary = []
        for s in w.sets:
            sets_summary.append(
                f"{s.exercise.name}: {s.reps}x{s.weight}kg"
                + (f" RPE {s.rpe}" if s.rpe else "")
            )
        sets_text = ", ".join(sets_summary) if sets_summary else "sin series"
        bw = f" | Peso corporal: {w.bodyweight}kg" if w.bodyweight else ""
        lines.append(f"  - {date_str}{bw} → {sets_text}")

    return "\n".join(lines)


def _call_gemini(prompt: str) -> str:
    """Llama a Gemini y devuelve el texto de respuesta. Maneja errores comunes."""
    try:
        response = _client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
            config=_CONFIG,
        )
        return response.text
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="Límite de la API de Gemini alcanzado. Inténtalo en unos minutos.",
            )
        raise HTTPException(status_code=502, detail=f"Error al contactar con Gemini: {error_msg}")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse, summary="Chat general con la IA")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat libre con el asistente de fitness.
    Si incluyes `profile_id`, la IA tendrá contexto de tus últimos entrenos.
    """
    if request.profile_id:
        context = _build_profile_context(request.profile_id, db)
        prompt = f"{context}\n\nPregunta del usuario: {request.message}"
    else:
        prompt = request.message

    reply = _call_gemini(prompt)
    return ChatResponse(reply=reply)


@router.get(
    "/analyze/{profile_id}",
    response_model=AnalysisResponse,
    summary="Análisis automático del progreso del perfil",
)
def analyze_profile(profile_id: int, db: Session = Depends(get_db)):
    """
    Analiza los últimos 30 días de entrenos del perfil y devuelve:
    - Resumen de volumen y progresión
    - Puntos fuertes detectados
    - Sugerencias de mejora
    """
    context = _build_profile_context(profile_id, db)

    prompt = (
        f"{context}\n\n"
        "Analiza estos datos de entrenamiento y proporciona:\n"
        "1. Resumen breve del volumen y frecuencia\n"
        "2. Ejercicios donde se aprecia más progresión\n"
        "3. Posibles puntos débiles o desequilibrios\n"
        "4. 2-3 recomendaciones concretas para las próximas semanas\n"
        "Sé directo y práctico, sin preambles."
    )

    analysis = _call_gemini(prompt)
    return AnalysisResponse(analysis=analysis)


@router.get(
    "/suggest-workout/{profile_id}",
    response_model=AnalysisResponse,
    summary="Sugerencia del próximo entreno",
)
def suggest_next_workout(profile_id: int, db: Session = Depends(get_db)):
    """
    Basándose en el historial reciente, sugiere qué entrenar en la próxima sesión
    (grupos musculares, ejercicios, series/reps orientativas).
    """
    context = _build_profile_context(profile_id, db)

    last_workout = (
        db.query(models.Workout)
        .filter(models.Workout.profile_id == profile_id)
        .order_by(models.Workout.date.desc())
        .first()
    )

    rest_info = ""
    if last_workout:
        days_rest = (datetime.utcnow() - last_workout.date).days
        rest_info = f"\nÚltimo entreno hace {days_rest} día(s)."

    prompt = (
        f"{context}{rest_info}\n\n"
        "Basándote en el historial anterior, sugiere el próximo entreno:\n"
        "- Qué grupo(s) muscular(es) trabajar\n"
        "- 4-6 ejercicios específicos con series y repeticiones orientativas\n"
        "- Intensidad recomendada (RPE)\n"
        "Justifica brevemente por qué esta sesión tiene sentido dado el historial."
    )

    suggestion = _call_gemini(prompt)
    return AnalysisResponse(analysis=suggestion)