import logging
import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.database import Base, engine
from app.features.materias.router import router as materias_router
from app.features.recordatorios.router import router as recordatorios_router
from app.features.recursos.router import recursos_main_router as recursos_router
from app.features.auth.router import router as auth_ruoter
from app.shared.exceptions import APIException

logger = logging.getLogger("miifts")

Base.metadata.create_all(bind=engine)

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


@app.get("/")
def root():
    return {"mensaje": "miIFTS API funcionando"}


@app.get("/health")
def health():
    return {"status": "ok"}