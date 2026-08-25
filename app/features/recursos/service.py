from typing import List

from features.recursos.model import Recurso, Convenio, TalentoTech
from features.recursos.schema import RecursoCreate, ConvenioCreate, TalentoTechCreate
from features.recursos.repository import RecursoRepository, ConvenioRepository, TalentoTechRepository

class RecursoService:
    def __init__(self, repository: RecursoRepository):
        self.repository = repository
    
    def get_all(self) -> list[Recurso]:
        return self.repository.get_all()

    def get_by_usuario(self, usuario_id: int) -> list[Recurso]:
        return self.repository.get_recursos_by_usuario(usuario_id)

    def create(self, recurso: RecursoCreate) -> Recurso:
        return self.repository.create_recurso(recurso)

    def update(self, recurso_id: int, recurso: RecursoCreate) -> Recurso:
        return self.repository.update_recurso(recurso_id, recurso)

    def delete(self, recurso_id: int) -> None:
        return self.repository.delete_recurso(recurso_id)
    
    def get_by_id(self, recurso_id: int) -> Recurso:
        return self.repository.get_recurso_by_id(recurso_id)

    def get_by_materia(self, materia_id: int) -> list[Recurso]:
        return self.repository.get_recurso_by_materia(materia_id)

class ConvenioService:
    def __init__(self, repository: ConvenioRepository):
        self.repository = repository

    def get_by_id(self, convenio_id: int) -> Convenio:
        return self.repository.get_convenio_by_id(convenio_id)
    
    def get_all(self) -> list[Convenio]:
        return self.repository.get_all()
    
    def get_by_carrera(self, carrera_id: int) -> list[Convenio]:
        return self.repository.get_convenios_by_carrera(carrera_id)
    
    def create(self, convenio: ConvenioCreate) -> Convenio:
        return self.repository.create_convenio(convenio)

    def update(self, convenio_id: int, convenio: ConvenioCreate) -> Convenio:
        return self.repository.update_convenio(convenio_id, convenio)

    def delete(self, convenio_id: int) -> None:
        return self.repository.delete_convenio(convenio_id)

class TalentoTechService:
    def __init__(self, repository: TalentoTechRepository):
        self.repository = repository

    def get_all(self) -> list[TalentoTech]:
        return self.repository.get_all()

    def get_by_id(self, talentotech_id: int) -> TalentoTech:
        return self.repository.get_talentotech_by_id(talentotech_id)

    def get_by_carrera(self, carrera_id: int) -> list[TalentoTech]:
        return self.repository.get_talentotech_by_carrera(carrera_id)

    def get_by_categoria(self, categoria: str) -> list[TalentoTech]:
        return self.repository.get_talentotech_by_categoria(categoria)

    def create(self, talentotech: TalentoTechCreate) -> TalentoTech:
        return self.repository.create_talentotech(talentotech)

    def update(self, talentotech_id: int, talentotech: TalentoTechCreate) -> TalentoTech:
        return self.repository.update_talentotech(talentotech_id, talentotech)

    def delete(self, talentotech_id: int) -> None:
        return self.repository.delete_talentotech(talentotech_id)

    
