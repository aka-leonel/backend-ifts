from fastapi import APIRouter, Depends, status
from typing import Optional
from datetime import date

from app.features.recursos.service import RecursoService
from app.features.recursos import RecursoCreate, RecursoResponse
from app.features.recursos.dependencies import get_recurso_service
from app.features.auth.router import get_current_user
from app.features.auth.schema import UsuarioResponse
from app.shared.exceptions import ForbiddenError
from app.shared.schemas.pagination import PaginatedResponse
from app.shared.utils.pagination import PaginationParams

router = APIRouter(
    prefix="/recursos",
    tags=["recursos"]
)



@router.get("/usuario/{usuario_id}", response_model=PaginatedResponse[RecursoResponse])
def get_by_usuario(
    usuario_id: int,
    service_recurso: RecursoService = Depends(get_recurso_service),
    pagination: PaginationParams = Depends(),
):
    return service_recurso.get_by_usuario_paginado(usuario_id, pagination)

@router.get("/materia/{materia_id}", response_model=PaginatedResponse[RecursoResponse])
def get_by_materia(
    materia_id: int,
    service_recurso: RecursoService = Depends(get_recurso_service),
    pagination: PaginationParams = Depends(),
):
    return service_recurso.get_by_materia_paginado(materia_id, pagination)

@router.put("/{recurso_id}", response_model=RecursoResponse)
def update(
    recurso_id: int,
    recurso: RecursoCreate,
    current_user: UsuarioResponse = Depends(get_current_user),
    service_recurso: RecursoService = Depends(get_recurso_service),
):
    existente = service_recurso.get_by_id(recurso_id)
    if existente.usuario_id != current_user.id:
        raise ForbiddenError("No podés modificar un recurso de otro usuario")
    return service_recurso.update(recurso_id, recurso)

@router.delete("/{recurso_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    recurso_id: int,
    current_user: UsuarioResponse = Depends(get_current_user),
    service_recurso: RecursoService = Depends(get_recurso_service),
):
    existente = service_recurso.get_by_id(recurso_id)
    if existente.usuario_id != current_user.id:
        raise ForbiddenError("No podés eliminar un recurso de otro usuario")
    service_recurso.delete(recurso_id)

@router.get("/{recurso_id}", response_model=RecursoResponse)
def get_by_id(recurso_id: int, service_recurso: RecursoService = Depends(get_recurso_service)):
    return service_recurso.get_by_id(recurso_id)

@router.get("/", response_model=PaginatedResponse[RecursoResponse])
def get_all(
    materia_id: Optional[int] = None,
    tipo: Optional[str] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    service_recurso: RecursoService = Depends(get_recurso_service),
    pagination: PaginationParams = Depends(),
):
    return service_recurso.get_recursos_filtrados_paginado(
        materia_id, tipo, desde, hasta, pagination
    )

@router.post("/", response_model=RecursoResponse, status_code=status.HTTP_201_CREATED)
def create(recurso: RecursoCreate, current_user: UsuarioResponse = Depends(get_current_user), service_recurso: RecursoService = Depends(get_recurso_service)):
    usuario_id = current_user.id
    return service_recurso.create(recurso, usuario_id)
