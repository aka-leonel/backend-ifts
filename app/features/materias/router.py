from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.features.auth.dependencies import (
    get_current_user,
    require_admin,
    solo_propio_o_admin,
)
from app.features.auth.schema import UsuarioResponse
from app.features.materias import service
from app.features.materias.schema import (
    CarreraCreate,
    CarreraResponse,
    CarreraUpdate,
    CorrelativaResponse,
    MateriaCreate,
    MateriaResponse,
    MateriaSearchQuery,
    MateriaUpdate,
    MateriaUsuarioCreate,
    MateriaUsuarioResponse,
    MateriaUsuarioUpdate,
    PromedioResponse,
)
from app.shared.schemas.pagination import PaginatedResponse
from app.shared.utils.pagination import PaginationParams

router = APIRouter(
    prefix="/materias",
    tags=["materias"],
)


@router.get("/carreras", response_model=PaginatedResponse[CarreraResponse])
def get_carreras(
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(),
):
    return service.get_carreras(db, pagination)


@router.post("/carreras", response_model=CarreraResponse, status_code=status.HTTP_201_CREATED)
def crear_carrera(
    datos: CarreraCreate,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioResponse = Depends(require_admin),
):
    return service.create_carrera(db, datos)


@router.put("/carreras/{carrera_id}", response_model=CarreraResponse)
def actualizar_carrera(
    carrera_id: int,
    datos: CarreraUpdate,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioResponse = Depends(require_admin),
):
    return service.update_carrera(db, carrera_id, datos)


@router.delete("/carreras/{carrera_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_carrera(
    carrera_id: int,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioResponse = Depends(require_admin),
):
    service.delete_carrera(db, carrera_id)
    return None


@router.get("/carreras/{carrera_id}", response_model=CarreraResponse)
def get_carrera(carrera_id: int, db: Session = Depends(get_db)):
    """Detalle de una carrera. `404` si no existe. Lectura pública."""
    return service.get_carrera(db, carrera_id)


@router.get("/carrera/{carrera_id}", response_model=PaginatedResponse[MateriaResponse])
def get_materias_by_carrera(
    carrera_id: int,
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(),
):
    return service.get_materias_by_carrera_paginado(db, carrera_id, pagination)


@router.get("/buscar", response_model=PaginatedResponse[MateriaResponse])
def buscar_materias(
    q: str,
    anio: Optional[int] = None,
    cuatrimestre: Optional[int] = None,
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(),
):
    return service.buscar_materias(db, q, anio, cuatrimestre, pagination)


@router.get("/correlativas/{materia_id}", response_model=PaginatedResponse[CorrelativaResponse])
def get_correlativas(
    materia_id: int,
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(),
):
    return service.get_correlativas(db, materia_id, pagination)


@router.get("/usuario/{usuario_id}", response_model=PaginatedResponse[MateriaUsuarioResponse])
def get_materias_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(),
    usuario_actual: UsuarioResponse = Depends(solo_propio_o_admin),
):
    return service.get_materias_usuario(db, usuario_id, pagination)


@router.get("/promedio/{usuario_id}", response_model=PromedioResponse)
def get_promedio(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioResponse = Depends(solo_propio_o_admin),
):
    return service.calcular_promedio(db, usuario_id)


@router.post(
    "/usuario",
    response_model=MateriaUsuarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_materia_usuario(
    datos: MateriaUsuarioCreate,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioResponse = Depends(get_current_user),
):
    return service.add_materia_usuario(db, datos, usuario_actual.id)


@router.patch("/cursada/{materia_usuario_id}", response_model=MateriaUsuarioResponse)
def update_materia_usuario(
    materia_usuario_id: int,
    datos: MateriaUsuarioUpdate,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioResponse = Depends(get_current_user),
):
    return service.update_materia_usuario(
        db, materia_usuario_id, usuario_actual.id, datos
    )


@router.delete("/cursada/{materia_usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_materia_usuario(
    materia_usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioResponse = Depends(get_current_user),
):
    service.delete_materia_usuario(db, materia_usuario_id, usuario_actual.id)
    return None


@router.post("/", response_model=MateriaResponse, status_code=status.HTTP_201_CREATED)
def crear_materia(
    datos: MateriaCreate,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioResponse = Depends(require_admin),
):
    return service.create_materia(db, datos)


@router.get("/{materia_id}", response_model=MateriaResponse)
def get_materia(materia_id: int, db: Session = Depends(get_db)):
    """Detalle de una materia. `404` si no existe. Lectura pública."""
    return service.get_materia(db, materia_id)


@router.put("/{materia_id}", response_model=MateriaResponse)
def actualizar_materia(
    materia_id: int,
    datos: MateriaUpdate,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioResponse = Depends(require_admin),
):
    return service.update_materia(db, materia_id, datos)


@router.delete("/{materia_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_materia(
    materia_id: int,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioResponse = Depends(require_admin),
):
    service.delete_materia(db, materia_id)
    return None
