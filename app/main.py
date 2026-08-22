from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.features.recordatorios.router import router as recordatorios_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="miIFTS API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recordatorios_router)

@app.get("/")
def root():
    return {"mensaje": "miIFTS API funcionando"}