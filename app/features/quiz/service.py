import json
import logging
import os
from io import BytesIO

import httpx
from pydantic import ValidationError
from pypdf import PdfReader
from sqlalchemy.orm import Session
from pypdf.errors import PyPdfError

from app.features.quiz.model import QuizUso
from app.features.quiz.schema import QuizResponse
from app.shared.exceptions import APIException, BadRequestError
from app.shared.utils.tiempo import ahora_local

logger = logging.getLogger(__name__)

MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_CHARS = 30_000  # texto que se le manda a la IA (acota costo y cuota)
MIN_CHARS = 200
MAX_USOS_POR_DIA = 5
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
DEFAULT_MODEL = "gemini-3.1-flash-lite"


class ServicioIAError(APIException):
    status_code = 502
    default_detail = "El servicio de IA no está disponible, probá de nuevo en unos minutos"


class LimiteDiarioError(APIException):
    status_code = 429
    default_detail = f"Llegaste al límite de {MAX_USOS_POR_DIA} quizzes por día, probá mañana"


class ServicioIANoConfigurado(APIException):
    status_code = 503
    default_detail = "La generación de quizzes no está configurada"


def extraer_texto(contenido: bytes) -> str:
    if len(contenido) > MAX_PDF_BYTES:
        raise BadRequestError("El PDF supera el máximo de 10 MB")
    try:
        lector = PdfReader(BytesIO(contenido))
        paginas = [p.extract_text() or "" for p in lector.pages]
    except (PyPdfError, ValueError, OSError):
        raise BadRequestError("No se pudo leer el archivo: no es un PDF válido")
    texto = "\n".join(paginas).strip()
    if len(texto) < MIN_CHARS:
        raise BadRequestError(
            "El PDF no tiene texto suficiente (puede ser un escaneo o imágenes)"
        )
    return texto[:MAX_CHARS]


def _prompt(texto: str, cantidad: int) -> str:
    return (
        f"Generá {cantidad} preguntas de opción múltiple en español basadas SOLO en el "
        "texto de abajo. Cada pregunta tiene exactamente 4 opciones y una sola correcta. "
        'Respondé únicamente con JSON: {"preguntas": [{"enunciado": str, "opciones": '
        '[str, str, str, str], "correcta": <índice 0-3>, "explicacion": str}]}.\n\n'
        f"TEXTO:\n{texto}"
    )


def _limpiar_json(contenido: str) -> str:
    contenido = contenido.strip()
    if contenido.startswith("```"):
        contenido = contenido.strip("`")
        contenido = contenido.removeprefix("json").strip()
    return contenido


def _usos_de_hoy(db: Session, usuario_id: int) -> int:
    inicio_dia = ahora_local().replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(QuizUso)
        .filter(QuizUso.usuario_id == usuario_id, QuizUso.fecha >= inicio_dia)
        .count()
    )


def generar_quiz(
    db: Session, usuario_id: int, contenido_pdf: bytes, cantidad: int
) -> QuizResponse:
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise ServicioIANoConfigurado()
    if _usos_de_hoy(db, usuario_id) >= MAX_USOS_POR_DIA:
        raise LimiteDiarioError()
    texto = extraer_texto(contenido_pdf)
    base_url = os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    modelo = os.getenv("LLM_MODEL", DEFAULT_MODEL)

    try:
        resp = httpx.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": modelo,
                "messages": [{"role": "user", "content": _prompt(texto, cantidad)}],
                "response_format": {"type": "json_object"},
                "temperature": 0.4,
            },
            timeout=60,
        )
        resp.raise_for_status()
        crudo = resp.json()["choices"][0]["message"]["content"]
        quiz = QuizResponse.model_validate(json.loads(_limpiar_json(crudo)))
    except (httpx.HTTPError, KeyError, IndexError, ValueError, ValidationError) as e:
        # ValueError cubre JSON inválido; no se loguea el texto del alumno ni la key
        estado = e.response.status_code if isinstance(e, httpx.HTTPStatusError) else "-"
        logger.error("Falló la generación de quiz: %s (HTTP %s)", type(e).__name__, estado)
        raise ServicioIAError()

    # Solo cuentan los quizzes generados con éxito: si la IA falla, no se gasta un uso
    db.add(QuizUso(usuario_id=usuario_id, fecha=ahora_local()))
    db.commit()
    return quiz
