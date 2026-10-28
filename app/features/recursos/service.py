from __future__ import annotations

from typing import List, Optional
from datetime import date

from app.features.recursos.model import Recurso, Convenio, TalentoTech
from app.features.recursos.schema import RecursoCreate, ConvenioCreate, ConvenioUpdate, TalentoTechCreate
from app.features.recursos.repository import RecursoRepository, ConvenioRepository, TalentoTechRepository
from app.shared.exceptions import DomainValidationError, DuplicateError, NotFoundError
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

    def _validar_carreras(self, carrera_ids: Optional[list[int]]) -> list[int]:
        """D17: deduplica preservando orden y valida que todos los ids existan."""
        if not carrera_ids:
            return []
        deduplicados = list(dict.fromkeys(carrera_ids))
        existentes = self.repository.carreras_existentes(deduplicados)
        faltantes = [cid for cid in deduplicados if cid not in existentes]
        if faltantes:
            if len(faltantes) == 1:
                raise DomainValidationError(f"No existe la carrera {faltantes[0]}")
            raise DomainValidationError(
                "No existen las carreras: " + ", ".join(str(cid) for cid in faltantes)
            )
        return deduplicados

    def _resolver_conjunto(
        self, carrera_ids: Optional[list[int]], todas_las_carreras: bool
    ) -> list[int]:
        """Aplica la invariante flag↔ids y devuelve los ids finales.

        `todas_las_carreras=True` ⇒ sin ids y sin filas explícitas.
        `False` ⇒ al menos una carrera.
        """
        if todas_las_carreras:
            if carrera_ids:
                raise DomainValidationError(
                    "Si 'todas_las_carreras' es true no se debe enviar 'carrera_ids'"
                )
            return []
        ids = self._validar_carreras(carrera_ids)
        if not ids:
            raise DomainValidationError(
                "Debe indicar al menos una carrera en 'carrera_ids' o marcar "
                "'todas_las_carreras'"
            )
        return ids

    def _validar_unicidad(
        self,
        institucion: str,
        carrera_destino: str,
        exclude_id: Optional[int] = None,
    ) -> None:
        """D17: no se permite duplicar (institucion, carrera_destino)."""
        existente = self.repository.get_by_unique_key(
            institucion, carrera_destino, exclude_id=exclude_id
        )
        if existente is not None:
            raise DuplicateError(
                "Ya existe un convenio con la misma institución y carrera destino"
            )

    def get_all(self) -> list[Convenio]:
        return self.repository.get_all()

    def get_all_paginado(
        self, params: PaginationParams, q: Optional[str] = None
    ) -> PaginatedResponse[Convenio]:
        return paginate(self.repository.query_all(q=q), params)

    def get_by_carrera(self, carrera_id: int, q: Optional[str] = None) -> list[Convenio]:
        return self.repository.get_convenios_by_carrera(carrera_id, q=q)

    def get_by_carrera_paginado(
        self, carrera_id: int, params: PaginationParams, q: Optional[str] = None
    ) -> PaginatedResponse[Convenio]:
        return paginate(self.repository.query_by_carrera(carrera_id, q=q), params)

    def create(self, convenio: ConvenioCreate) -> Convenio:
        ids = self._resolver_conjunto(
            convenio.carrera_ids, convenio.todas_las_carreras
        )
        self._validar_unicidad(convenio.institucion, convenio.carrera_destino)
        carreras = self.repository.get_carreras(ids)
        return self.repository.create_convenio(convenio, carreras)

    def update(self, convenio_id: int, convenio: ConvenioCreate) -> Convenio:
        self.get_by_id(convenio_id)
        ids = self._resolver_conjunto(
            convenio.carrera_ids, convenio.todas_las_carreras
        )
        self._validar_unicidad(
            convenio.institucion,
            convenio.carrera_destino,
            exclude_id=convenio_id,
        )
        carreras = self.repository.get_carreras(ids)
        return self.repository.update_convenio(convenio_id, convenio, carreras)

    def update_parcial(self, convenio_id: int, convenio: ConvenioUpdate) -> Convenio:
        """D16/D17: PATCH. Body vacío devuelve el convenio sin cambios."""
        actual = self.get_by_id(convenio_id)
        datos = convenio.model_dump(exclude_unset=True)
        # Un `null` explícito no puede persistirse: las columnas son NOT NULL.
        datos = {campo: valor for campo, valor in datos.items() if valor is not None}
        if not datos:
            return actual

        ids_actuales = [carrera.id for carrera in actual.carreras]
        flag_final = datos.get("todas_las_carreras", actual.todas_las_carreras)
        ids_presente = "carrera_ids" in datos
        carreras: Optional[list] = None

        if flag_final:
            if ids_presente and datos["carrera_ids"]:
                raise DomainValidationError(
                    "Si 'todas_las_carreras' es true no se debe enviar 'carrera_ids'"
                )
            # Pasar a wildcard limpia las filas explícitas.
            if ids_presente or not actual.todas_las_carreras:
                carreras = []
        else:
            if ids_presente:
                ids_finales = self._validar_carreras(datos["carrera_ids"])
                if not ids_finales:
                    raise DomainValidationError(
                        "Debe indicar al menos una carrera en 'carrera_ids' o marcar "
                        "'todas_las_carreras'"
                    )
                carreras = self.repository.get_carreras(ids_finales)
            elif not ids_actuales:
                raise DomainValidationError(
                    "Debe indicar al menos una carrera en 'carrera_ids' o marcar "
                    "'todas_las_carreras'"
                )
            # Si no viene `carrera_ids`, se conservan las carreras actuales.

        # Se combina con el estado actual para detectar colisiones al editar
        # sólo parte de la clave única.
        self._validar_unicidad(
            datos.get("institucion", actual.institucion),
            datos.get("carrera_destino", actual.carrera_destino),
            exclude_id=convenio_id,
        )
        return self.repository.update_convenio_parcial(
            convenio_id, datos, carreras
        )

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

    def get_by_carrera_paginado(
        self, carrera_id: int, params: PaginationParams
    ) -> PaginatedResponse[TalentoTech]:
        return paginate(self.repository.query_by_carrera(carrera_id), params)

    def get_by_categoria(self, categoria: str) -> list[TalentoTech]:
        return self.repository.get_talentotech_by_categoria(categoria)

    def get_by_categoria_paginado(
        self, categoria: str, params: PaginationParams
    ) -> PaginatedResponse[TalentoTech]:
        return paginate(self.repository.query_by_categoria(categoria), params)

    def create(self, talentotech: TalentoTechCreate) -> TalentoTech:
        return self.repository.create_talentotech(talentotech)

    def update(self, talentotech_id: int, talentotech: TalentoTechCreate) -> TalentoTech:
        self.get_by_id(talentotech_id)
        return self.repository.update_talentotech(talentotech_id, talentotech)

    def delete(self, talentotech_id: int) -> None:
        self.get_by_id(talentotech_id)
        return self.repository.delete_talentotech(talentotech_id)

    
