from datetime import date
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.features.auth.dependencies import get_current_user
from app.features.auth.schema import UsuarioResponse
from app.features.recordatorios import service
from app.features.recordatorios.schema import RecordatorioCreate, RecordatorioResponse
from app.shared.schemas.pagination import PaginatedResponse
from app.shared.utils.pagination import PaginationParams

router = APIRouter(
    prefix="/recordatorios",
    tags=["recordatorios"]
)

@router.get("/", response_model=PaginatedResponse[RecordatorioResponse])
def get_recordatorios(
    tipo: Optional[str] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    materia_id: Optional[int] = None,
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(),
    current_user: UsuarioResponse = Depends(get_current_user),
):
    return service.get_recordatorios_filtrados_paginado(
        db, current_user.id, tipo, desde, hasta, materia_id, pagination
    )

@router.post("/", response_model=RecordatorioResponse, status_code=status.HTTP_201_CREATED)
def create_recordatorio(
    recordatorio: RecordatorioCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user),
):
    return service.create_recordatorio(db, recordatorio, current_user.id)

@router.delete("/{recordatorio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recordatorio(
    recordatorio_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user),
):
    service.delete_recordatorio(db, recordatorio_id, current_user.id)
    return None