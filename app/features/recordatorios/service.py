from __future__ import annotations

from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from app.features.recordatorios.repository import RecordatorioRepository
from app.features.recordatorios.model import Recordatorio
from app.features.recordatorios.schema import RecordatorioCreate
from app.shared.exceptions import NotFoundError
from app.shared.schemas.pagination import PaginatedResponse
from app.shared.utils.pagination import PaginationParams, paginate

def get_recordatorios(db: Session, usuario_id: int):
    repo = RecordatorioRepository(db)
    return repo.get_by_usuario(usuario_id)

def get_recordatorios_filtrados(db: Session, usuario_id: int, tipo: Optional[str], desde: Optional[date], hasta: Optional[date], materia_id: Optional[int]):
    repo = RecordatorioRepository(db)
    return repo.search(usuario_id, tipo, desde, hasta, materia_id)


def get_recordatorios_filtrados_paginado(
    db: Session,
    usuario_id: int,
    tipo: Optional[str],
    desde: Optional[date],
    hasta: Optional[date],
    materia_id: Optional[int],
    params: PaginationParams,
) -> PaginatedResponse[Recordatorio]:
    repo = RecordatorioRepository(db)
    query = repo.query_search(usuario_id, tipo, desde, hasta, materia_id)
    return paginate(query, params)

def create_recordatorio(db: Session, recordatorio: RecordatorioCreate, usuario_id: int):
    repo = RecordatorioRepository(db)
    nuevo = Recordatorio(
        titulo=recordatorio.titulo,
        fecha=recordatorio.fecha,
        tipo=recordatorio.tipo,
        materia_id=recordatorio.materia_id,
        usuario_id=usuario_id
    )
    return repo.create(nuevo)

def delete_recordatorio(db: Session, recordatorio_id: int, usuario_id: int):
    repo = RecordatorioRepository(db)
    eliminado = repo.delete(recordatorio_id, usuario_id)
    if eliminado is None:
        raise NotFoundError("Recordatorio no encontrado")
    return eliminado