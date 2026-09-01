from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
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
    usuario_id: int,
    tipo: Optional[str] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    materia_id: Optional[int] = None,
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(),
):
    return service.get_recordatorios_filtrados_paginado(
        db, usuario_id, tipo, desde, hasta, materia_id, pagination
    )

@router.post("/", response_model=RecordatorioResponse)
def create_recordatorio(
    recordatorio: RecordatorioCreate,
    usuario_id: int,
    db: Session = Depends(get_db)
):
    return service.create_recordatorio(db, recordatorio, usuario_id)

@router.delete("/{recordatorio_id}")
def delete_recordatorio(
    recordatorio_id: int,
    usuario_id: int,
    db: Session = Depends(get_db)
):
    resultado = service.delete_recordatorio(db, recordatorio_id, usuario_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")
    return {"ok": True}