import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.features.materias.router import router as materias_router
from app.features.recordatorios.router import router as recordatorios_router
from app.features.recursos.router import recursos_main_router as recursos_router
from app.features.auth.router import router as auth_ruoter
from app.features.notificaciones.router import router as notificaciones_router
from app.shared.exceptions import APIException

# Sin esto, el logger raíz queda en WARNING por defecto y todos los
# logger.info() de la app (incluido el de reset de contraseña) se
# descartan en silencio, sin llegar nunca a la consola.
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("miifts")

# APScheduler import condicional (se instala en NOTIF-008)
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from app.features.notificaciones.scheduler import check_and_send_reminder_notifications_default
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    AsyncIOScheduler = None  # type: ignore
    check_and_send_reminder_notifications_default = None  # type: ignore

scheduler: AsyncIOScheduler | None = None


def _get_scheduler_interval_minutes() -> int:
    """Obtiene el intervalo del scheduler desde variable de entorno (default 5 min)."""
    value = os.getenv("PUSH_SCHEDULER_INTERVAL_MINUTES", "5")
    try:
        return int(value)
    except ValueError:
        logger.warning(
            "Valor inválido para PUSH_SCHEDULER_INTERVAL_MINUTES: '%s', usando default 5",
            value,
        )
        return 5


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación: scheduler de notificaciones."""
    global scheduler
    
    # Startup
    if APSCHEDULER_AVAILABLE:
        interval_minutes = _get_scheduler_interval_minutes()
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            check_and_send_reminder_notifications_default,
            "interval",
            minutes=interval_minutes,
            id="push_reminder_job",
            replace_existing=True,
        )
        scheduler.start()
        logger.info(
            "Scheduler de notificaciones push iniciado (intervalo: %d min)",
            interval_minutes,
        )
    else:
        logger.warning(
            "apscheduler no está instalado; el job periódico de recordatorios no se ejecutará. "
            "Instala con: pip install apscheduler"
        )
    
    yield
    
    # Shutdown
    if scheduler is not None:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler de notificaciones push detenido")

ORIGENES_PERMITIDOS = [
    origen.strip()
    for origen in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origen.strip()
]

app = FastAPI(
    title="miIFTS API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES_PERMITIDOS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handler central de las excepciones de dominio.

    FastAPI ya sabe serializar `APIException` (hereda de HTTPException); acá
    solo agregamos logging para trazabilidad y devolvemos el mismo formato
    `{"detail": ...}` de siempre.
    """
    logger.info("APIException %s en %s: %s", exc.status_code, request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


def _campo_de_loc(loc) -> str:
    """Nombre de campo legible a partir del `loc` de Pydantic
    (descarta el prefijo body/query/path)."""
    partes = [
        str(p)
        for p in loc
        if p not in ("body", "query", "path", "header", "cookie")
    ]
    return ".".join(partes) or "(request)"


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Unifica los 422 de Pydantic al mismo formato que el resto de la API:
    `detail` siempre string, y `errors` con el detalle campo por campo."""
    errores = [
        {
            "campo": _campo_de_loc(e.get("loc", ())),
            "msg": e.get("msg", "Dato inválido").removeprefix("Value error, "),
        }
        for e in exc.errors()
    ]
    detail = errores[0]["msg"] if errores else "Datos inválidos"
    logger.info("ValidationError en %s: %s", request.url.path, errores)
    return JSONResponse(
        status_code=422,
        content={"detail": detail, "errors": errores},
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Cualquier violación de integridad de la DB que se escape de los services
    se traduce a un 409 legible en vez de un 500."""
    logger.warning("IntegrityError en %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=409,
        content={"detail": "Conflicto de integridad de datos"},
    )


app.include_router(recordatorios_router)
app.include_router(materias_router)
app.include_router(recursos_router)
app.include_router(auth_ruoter)
app.include_router(notificaciones_router)


@app.get("/")
def root():
    return {"mensaje": "miIFTS API funcionando"}


@app.get("/health")
def health():
    return {"status": "ok"}