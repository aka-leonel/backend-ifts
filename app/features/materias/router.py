from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.features.materias import service
from app.features.materias.schema import (
    CarreraResponse,
    CorrelativaResponse,
    MateriaResponse,
    MateriaUsuarioCreate,
    MateriaUsuarioResponse,
    MateriaUsuarioUpdate,
    PromedioResponse,
)

router = APIRouter(
    prefix="/materias",
    tags=["materias"],
)


def get_usuario_actual() -> int:
    return 1


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


@router.get("/promedio/{usuario_id}", response_model=PromedioResponse)
def get_promedio(usuario_id: int, db: Session = Depends(get_db)):
    return service.calcular_promedio(db, usuario_id)


@router.post(
    "/usuario/{usuario_id}",
    response_model=MateriaUsuarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_materia_usuario(
    usuario_id: int,
    datos: MateriaUsuarioCreate,
    db: Session = Depends(get_db),
):
    try:
        return service.add_materia_usuario(db, datos, usuario_id)
    except service.MateriaNoEncontrada as error:
        raise HTTPException(status_code=404, detail=str(error))
    except service.MateriaYaCargada as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.patch("/cursada/{materia_usuario_id}", response_model=MateriaUsuarioResponse)
def update_materia_usuario(
    materia_usuario_id: int,
    datos: MateriaUsuarioUpdate,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_usuario_actual),
):
    resultado = service.update_materia_usuario(
        db, materia_usuario_id, usuario_id, datos
    )
    if resultado is None:
        raise HTTPException(status_code=404, detail="No se encontró esa cursada")
    return resultado


@router.delete("/cursada/{materia_usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_materia_usuario(
    materia_usuario_id: int,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_usuario_actual),
):
    resultado = service.delete_materia_usuario(db, materia_usuario_id, usuario_id)
    if resultado is None:
        raise HTTPException(status_code=404, detail="No se encontró esa cursada")
    return None