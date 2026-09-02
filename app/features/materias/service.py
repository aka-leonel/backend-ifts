from __future__ import annotations

from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.features.auth.repository import AuthRepository
from app.features.materias.model import Carrera, Correlativa, Materia, MateriaUsuario
from app.features.materias.repository import (
    CarreraRepository,
    CorrelativaRepository,
    MateriaRepository,
    MateriaUsuarioRepository,
)
from app.features.materias.schema import (
    CarreraCreate,
    CarreraUpdate,
    MateriaCreate,
    MateriaUpdate,
    MateriaUsuarioCreate,
    MateriaUsuarioUpdate,
)
from app.shared.exceptions import BusinessRuleError, DuplicateError, NotFoundError
from app.shared.schemas.pagination import PaginatedResponse
from app.shared.utils.pagination import PaginationParams, paginate


def get_carreras(db: Session) -> list[Carrera]:
    return CarreraRepository(db).get_all()


def create_carrera(db: Session, datos: CarreraCreate) -> Carrera:
    return CarreraRepository(db).create(datos)


def update_carrera(db: Session, carrera_id: int, datos: CarreraUpdate) -> Carrera:
    carrera = CarreraRepository(db).update(carrera_id, datos)
    if carrera is None:
        raise NotFoundError("Carrera no encontrada")
    return carrera


def delete_carrera(db: Session, carrera_id: int) -> Carrera:
    repo = CarreraRepository(db)
    carrera = repo.get_by_id(carrera_id)
    if carrera is None:
        raise NotFoundError("Carrera no encontrada")

    if MateriaRepository(db).query_by_carrera(carrera_id).count() > 0:
        raise BusinessRuleError(
            "No se puede eliminar una carrera con materias asociadas"
        )

    return repo.delete(carrera_id)


def get_materias_by_carrera(db: Session, carrera_id: int) -> list[Materia]:
    return MateriaRepository(db).get_by_carrera(carrera_id)


def buscar_materias(db: Session, q: str, anio: Optional[int], cuatrimestre: Optional[int]) -> list[Materia]:
    return MateriaRepository(db).search(q, anio, cuatrimestre)


def get_materias_by_carrera_paginado(
    db: Session, carrera_id: int, params: PaginationParams
) -> PaginatedResponse[Materia]:
    query = MateriaRepository(db).query_by_carrera(carrera_id)
    return paginate(query, params)


def create_materia(db: Session, datos: MateriaCreate) -> Materia:
    try:
        return MateriaRepository(db).create(datos)
    except IntegrityError:
        db.rollback()
        raise DuplicateError(
            f"Ya existe una materia con código '{datos.codigo}' en esa carrera"
        )


def update_materia(db: Session, materia_id: int, datos: MateriaUpdate) -> Materia:
    materia = MateriaRepository(db).update(materia_id, datos)
    if materia is None:
        raise NotFoundError("Materia no encontrada")
    return materia


def delete_materia(db: Session, materia_id: int) -> Materia:
    repo = MateriaRepository(db)
    materia = repo.get_by_id(materia_id)
    if materia is None:
        raise NotFoundError("Materia no encontrada")

    if MateriaUsuarioRepository(db).count_by_materia(materia_id) > 0:
        raise BusinessRuleError(
            "No se puede eliminar una materia con cursadas asociadas"
        )

    return repo.delete(materia_id)


def get_correlativas(db: Session, materia_id: int) -> list[Correlativa]:
    return CorrelativaRepository(db).get_by_materia(materia_id)


def get_materias_usuario(db: Session, usuario_id: int) -> list[MateriaUsuario]:
    return MateriaUsuarioRepository(db).get_by_usuario(usuario_id)


def add_materia_usuario(
    db: Session, datos: MateriaUsuarioCreate, usuario_id: int
) -> MateriaUsuario:
    usuario = AuthRepository(db).get_by_id(usuario_id)
    if usuario is None:
        raise NotFoundError("Usuario no encontrado")

    materia = MateriaRepository(db).get_by_id(datos.materia_id)
    if materia is None:
        raise NotFoundError(f"No existe la materia {datos.materia_id}")

    if materia.carrera_id != usuario.carrera_id:
        raise BusinessRuleError("La materia no pertenece a la carrera del alumno")

    repo = MateriaUsuarioRepository(db)
    if repo.get_by_usuario_y_materia(usuario_id, datos.materia_id) is not None:
        raise DuplicateError("Esa materia ya está cargada")

    nueva = MateriaUsuario(usuario_id=usuario_id, **datos.model_dump())

    try:
        return repo.create(nueva)
    except IntegrityError:
        db.rollback()
        raise DuplicateError("Esa materia ya está cargada")


def update_materia_usuario(
    db: Session,
    materia_usuario_id: int,
    usuario_id: int,
    datos: MateriaUsuarioUpdate,
) -> MateriaUsuario:
    cursada = MateriaUsuarioRepository(db).update(materia_usuario_id, usuario_id, datos)
    if cursada is None:
        raise NotFoundError("No se encontró esa cursada")
    return cursada


def delete_materia_usuario(
    db: Session, materia_usuario_id: int, usuario_id: int
) -> MateriaUsuario:
    cursada = MateriaUsuarioRepository(db).delete(materia_usuario_id, usuario_id)
    if cursada is None:
        raise NotFoundError("No se encontró esa cursada")
    return cursada


def calcular_promedio(db: Session, usuario_id: int) -> dict:
    cursadas = MateriaUsuarioRepository(db).get_by_usuario(usuario_id)
    computadas = [c for c in cursadas if c.nota_final is not None]

    if not computadas:
        return {"promedio": None, "materias_computadas": 0}

    promedio = sum(c.nota_final for c in computadas) / len(computadas)
    return {"promedio": round(promedio, 2), "materias_computadas": len(computadas)}
