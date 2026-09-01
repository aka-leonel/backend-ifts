from typing import List
from app.shared.schemas.pagination import PaginatedResponse
import math
from app.features.recursos.model import Recurso, Convenio, TalentoTech
from app.features.recursos.schema import RecursoCreate, ConvenioCreate, TalentoTechCreate, RecursoResponse, ConvenioResponse, TalentoTechResponse
from app.features.recursos.repository import RecursoRepository, ConvenioRepository, TalentoTechRepository

class RecursoNotFound(Exception):
    pass

class ConvenioNotFound(Exception):
    pass

class TalentoTechNotFound(Exception):
    pass

# --- RecursoService ---
class RecursoService:
    def __init__(self, repository: RecursoRepository):
        self.repository = repository
    
    def get_all_paginated(self, page: int, per_page: int) -> PaginatedResponse[RecursoResponse]:
        items, total = self.repository.get_all_paginated(page=page, per_page=per_page)
        total_pages = math.ceil(total / per_page) if total > 0 else 0

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

    def get_by_usuario(self, usuario_id: int) -> list[Recurso]:
        return self.repository.get_recursos_by_usuario(usuario_id)

    def create(self, recurso: RecursoCreate, usuario_id: int) -> Recurso:
        return self.repository.create_recurso(recurso, usuario_id)

    def update(self, recurso_id: int, recurso: RecursoCreate) -> Recurso:
        self.get_by_id(recurso_id)
        return self.repository.update_recurso(recurso_id, recurso)

    def delete(self, recurso_id: int) -> None:
        self.get_by_id(recurso_id) 
        return self.repository.delete_recurso(recurso_id)
    
    def get_by_id(self, recurso_id: int) -> Recurso:
        recurso_valid = self.repository.get_recurso_by_id(recurso_id)
        if recurso_valid is None:
            raise RecursoNotFound(f"No se encontró el recurso {recurso_id}")
        return recurso_valid

    def get_by_materia(self, materia_id: int) -> list[Recurso]:
        return self.repository.get_recurso_by_materia(materia_id)

# --- ConvenioService ---
class ConvenioService:
    def __init__(self, repository: ConvenioRepository):
        self.repository = repository

    def get_all_paginated(self, page: int, per_page: int) -> PaginatedResponse[ConvenioResponse]:
        items, total = self.repository.get_all_paginated(page=page, per_page=per_page)
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

    def get_by_id(self, convenio_id: int) -> Convenio:
        convenio_valid = self.repository.get_convenio_by_id(convenio_id)
        if convenio_valid is None:
            raise ConvenioNotFound(f"No se encontró el convenio {convenio_id}")
        return convenio_valid
    
# --- TalentoTechService ---
class TalentoTechService:
    def __init__(self, repository: TalentoTechRepository):
        self.repository = repository
    
    def get_all_paginated(self, page: int, per_page: int) -> PaginatedResponse[TalentoTechResponse]:
        items, total = self.repository.get_all_paginated(page=page, per_page=per_page)
        total_pages = math.ceil(total / per_page) if total > 0 else 0

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )

    def get_by_id(self, talentotech_id: int) -> TalentoTech:
        talentotech_valid = self.repository.get_talentotech_by_id(talentotech_id)
        if talentotech_valid is None:
            raise TalentoTechNotFound(f"No se encontró el talentotech con ID: {talentotech_id}")
        return talentotech_valid
