from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.features.recursos.service import RecursoService, RecursoNotFound
from app.features.recursos import RecursoCreate, RecursoResponse
from app.features.recursos.dependencies import get_recurso_service
from app.features.auth.router import get_current_user 
from app.features.auth.schema import UsuarioResponse

router = APIRouter(
    prefix="/recursos",
    tags=["recursos"]
)



@router.get("/usuario/{usuario_id}", response_model=List[RecursoResponse])
def get_by_usuario(usuario_id: int, service_recurso: RecursoService = Depends(get_recurso_service)):
    return service_recurso.get_by_usuario(usuario_id)

@router.get("/materia/{materia_id}", response_model=List[RecursoResponse])
def get_by_materia(materia_id: int, service_recurso: RecursoService = Depends(get_recurso_service)):
    return service_recurso.get_by_materia(materia_id)

@router.put("/{recurso_id}", response_model=RecursoResponse)
def update(recurso_id: int, recurso: RecursoCreate, service_recurso: RecursoService = Depends(get_recurso_service)):
    try:
        return service_recurso.update(recurso_id, recurso)
    except RecursoNotFound as err:
        raise HTTPException(status_code=404, detail=str(err))

@router.delete("/{recurso_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(recurso_id: int, service_recurso: RecursoService = Depends(get_recurso_service)):
    try:
        service_recurso.delete(recurso_id)
    except RecursoNotFound as err:
        raise HTTPException(status_code=404, detail=str(err))

@router.get("/{recurso_id}", response_model=RecursoResponse)
def get_by_id(recurso_id: int, service_recurso: RecursoService = Depends(get_recurso_service)):
    try:
        return service_recurso.get_by_id(recurso_id)
    except RecursoNotFound as err:
        raise HTTPException(status_code=404, detail=str(err))

@router.get("/", response_model=List[RecursoResponse])
def get_all(service_recurso: RecursoService = Depends(get_recurso_service)):
    return service_recurso.get_all()

@router.post("/", response_model=RecursoResponse, status_code=status.HTTP_201_CREATED)
def create(recurso: RecursoCreate, current_user: UsuarioResponse = Depends(get_current_user), service_recurso: RecursoService = Depends(get_recurso_service)): 
    usuario_id = current_user.id
    return service_recurso.create(recurso, usuario_id)

