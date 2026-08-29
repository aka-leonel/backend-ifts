import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.features.materias.router import router as materias_router
from app.features.recordatorios.router import router as recordatorios_router
from app.features.recursos.router import recursos_main_router as recursos_router
from app.features.auth.router import router as auth_router

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

app.include_router(recordatorios_router)
app.include_router(materias_router)
app.include_router(recursos_router)
app.include_router(auth_router)


@app.get("/")
def root():
    return {"mensaje": "miIFTS API funcionando"}


@app.get("/health")
def health():
    return {"status": "ok"}