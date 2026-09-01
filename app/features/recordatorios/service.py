import math
from sqlalchemy.orm import Session
from app.features.recordatorios.repository import RecordatorioRepository
from app.features.recordatorios.model import Recordatorio
from app.features.recordatorios.schema import RecordatorioCreate
from app.shared.schemas.pagination import PaginatedResponse


def get_recordatorios_paginated(db: Session, usuario_id: int, page: int, per_page: int):
    repo = RecordatorioRepository(db)

    # 1. Obtener los items para la página actual
    items = repo.get_paginated_by_usuario(
        usuario_id=usuario_id, 
        page=page, 
        per_page=per_page
    )

    # 2. Obtener la cantidad total de items
    total_items = repo.count_by_usuario(usuario_id=usuario_id)

    # 3. Calcular el total de páginas
    total_pages = math.ceil(total_items / per_page)

    # 4. Construir la respuesta paginada
    return PaginatedResponse(
        items=items,
        total=total_items,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

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
    return repo.delete(recordatorio_id, usuario_id)