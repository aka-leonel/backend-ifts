from typing import List, Optional
from datetime import date

from app.features.recursos.model import Recurso, Convenio, TalentoTech
from app.features.recursos.schema import RecursoCreate, ConvenioCreate, TalentoTechCreate
from app.features.recursos.repository import RecursoRepository, ConvenioRepository, TalentoTechRepository
from app.shared.exceptions import DuplicateError, NotFoundError
from app.shared.schemas.pagination import PaginatedResponse
from app.shared.utils.pagination import PaginationParams, paginate

# Alias retrocompatibles: el resto del código (y algún import viejo) usa estos
# nombres; ahora todos resuelven a la jerarquía única de app.shared.exceptions.
RecursoNotFound = NotFoundError
ConvenioNotFound = NotFoundError
TalentoTechNotFound = NotFoundError
RecursoAlreadyExists = DuplicateError
ConvenioAlreadyExists = DuplicateError
TalentoTechAlreadyExists = DuplicateError

class RecursoService:
    def __init__(self, repository: RecursoRepository):
        self.repository = repository
    
    def get_all(self) -> list[Recurso]:
        return self.repository.get_all()

    def get_all_paginado(self, params: PaginationParams) -> PaginatedResponse[Recurso]:
        return paginate(self.repository.query_all(), params)

    def get_by_usuario(self, usuario_id: int) -> list[Recurso]:
        return self.repository.get_recursos_by_usuario(usuario_id)

    def get_by_usuario_paginado(
        self, usuario_id: int, params: PaginationParams
    ) -> PaginatedResponse[Recurso]:
        return paginate(self.repository.query_by_usuario(usuario_id), params)

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
            raise NotFoundError(f"No se encontró el recurso {recurso_id}")
        return recurso_valid

    def get_by_materia(self, materia_id: int) -> list[Recurso]:
        return self.repository.get_recurso_by_materia(materia_id)

    def get_recursos_filtrados(self, materia_id: Optional[int], tipo: Optional[str], desde: Optional[date], hasta: Optional[date]) -> list[Recurso]:
        return self.repository.filter_recursos(materia_id, tipo, desde, hasta)

    def get_recursos_filtrados_paginado(
        self,
        materia_id: Optional[int],
        tipo: Optional[str],
        desde: Optional[date],
        hasta: Optional[date],
        params: PaginationParams,
    ) -> PaginatedResponse[Recurso]:
        query = self.repository.query_filtered(materia_id, tipo, desde, hasta)
        return paginate(query, params)

    def get_by_materia_paginado(
        self, materia_id: int, params: PaginationParams
    ) -> PaginatedResponse[Recurso]:
        return paginate(self.repository.query_by_materia(materia_id), params)

class ConvenioService:
    def __init__(self, repository: ConvenioRepository):
        self.repository = repository

    def get_by_id(self, convenio_id: int) -> Convenio:
        convenio_valid = self.repository.get_convenio_by_id(convenio_id)
        if convenio_valid is None:
            raise NotFoundError(f"No se encontró el convenio {convenio_id}")

        return convenio_valid
    
    def get_all(self) -> list[Convenio]:
        return self.repository.get_all()

    def get_all_paginado(self, params: PaginationParams) -> PaginatedResponse[Convenio]:
        return paginate(self.repository.query_all(), params)

    def get_by_carrera(self, carrera_id: int) -> list[Convenio]:
        return self.repository.get_convenios_by_carrera(carrera_id)
    
    def create(self, convenio: ConvenioCreate) -> Convenio:
        return self.repository.create_convenio(convenio)

    def update(self, convenio_id: int, convenio: ConvenioCreate) -> Convenio:
        self.get_by_id(convenio_id)
        return self.repository.update_convenio(convenio_id, convenio)

    def delete(self, convenio_id: int) -> None:
        self.get_by_id(convenio_id)
        return self.repository.delete_convenio(convenio_id)

class TalentoTechService:
    def __init__(self, repository: TalentoTechRepository):
        self.repository = repository

    def get_all(self) -> list[TalentoTech]:
        return self.repository.get_all()

    def get_all_paginado(self, params: PaginationParams) -> PaginatedResponse[TalentoTech]:
        return paginate(self.repository.query_all(), params)

    def get_by_id(self, talentotech_id: int) -> TalentoTech:
        talentotech_valid = self.repository.get_talentotech_by_id(talentotech_id)
        if talentotech_valid is None:
            raise NotFoundError(f"No se encontró el talentotech con ID: {talentotech_id}")

        return talentotech_valid

    def get_by_carrera(self, carrera_id: int) -> list[TalentoTech]:
        return self.repository.get_talentotech_by_carrera(carrera_id)

    def get_by_categoria(self, categoria: str) -> list[TalentoTech]:
        return self.repository.get_talentotech_by_categoria(categoria)

    def create(self, talentotech: TalentoTechCreate) -> TalentoTech:
        return self.repository.create_talentotech(talentotech)

    def update(self, talentotech_id: int, talentotech: TalentoTechCreate) -> TalentoTech:
        self.get_by_id(talentotech_id)
        return self.repository.update_talentotech(talentotech_id, talentotech)

    def delete(self, talentotech_id: int) -> None:
        self.get_by_id(talentotech_id)
        return self.repository.delete_talentotech(talentotech_id)

    
