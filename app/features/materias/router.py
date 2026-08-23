from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.features.materias import service
from app.features.materias.schema import (
    CarreraResponse,
    MateriaResponse,
    CorrelativaResponse,
    MateriaUsuarioCreate,
    MateriaUsuarioUpdate,
    MateriaUsuarioResponse
)

router = APIRouter(
    prefix="/materias",
    tags=["materias"]
)

@router.get("/carreras", response_model=List[CarreraResponse])
def get_carreras(db: Session = Depends(get_db)):
    return service.get_carreras(db)

@router.get("/carrera/{carrera_id}", response_model=List[MateriaResponse])
def get_materias_by_carrera(carrera_id: int, db: Session = Depends(get_db)):
    return service.get_materias_by_carrera(db, carrera_id)

@router.get("/correlativas/{materia_id}", response_model=List[CorrelativaResponse])
def get_correlativas(materia_id: int, db: Session = Depends(get_db)):
    return service.get_correlativas(db, materia_id)

@router.get("/usuario/{usuario_id}", response_model=List[MateriaUsuarioResponse])
def get_materias_usuario(usuario_id: int, db: Session = Depends(get_db)):
    return service.get_materias_usuario(db, usuario_id)

@router.post("/usuario/{usuario_id}", response_model=MateriaUsuarioResponse)
def add_materia_usuario(
    usuario_id: int,
    datos: MateriaUsuarioCreate,
    db: Session = Depends(get_db)
):
    return service.add_materia_usuario(db, datos, usuario_id)

@router.patch("/usuario/{materia_usuario_id}", response_model=MateriaUsuarioResponse)
def update_materia_usuario(
    materia_usuario_id: int,
    usuario_id: int,
    datos: MateriaUsuarioUpdate,
    db: Session = Depends(get_db)
):
    resultado = service.update_materia_usuario(db, materia_usuario_id, usuario_id, datos)
    if not resultado:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    return resultado

@router.delete("/usuario/{materia_usuario_id}")
def delete_materia_usuario(
    materia_usuario_id: int,
    usuario_id: int,
    db: Session = Depends(get_db)
):
    resultado = service.delete_materia_usuario(db, materia_usuario_id, usuario_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    return {"ok": True}

@router.get("/promedio/{usuario_id}")
def get_promedio(usuario_id: int, db: Session = Depends(get_db)):
    promedio = service.calcular_promedio(db, usuario_id)
    return {"promedio": promedio}