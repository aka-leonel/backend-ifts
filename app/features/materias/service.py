from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.features.materias.model import Carrera, Correlativa, Materia, MateriaUsuario
from app.features.materias.repository import (
    CarreraRepository,
    CorrelativaRepository,
    MateriaRepository,
    MateriaUsuarioRepository,
)
from app.features.materias.schema import MateriaUsuarioCreate, MateriaUsuarioUpdate


class MateriaNoEncontrada(Exception):
    pass


class MateriaYaCargada(Exception):
    pass


def get_carreras(db: Session) -> list[Carrera]:
    return CarreraRepository(db).get_all()


def get_materias_by_carrera(db: Session, carrera_id: int) -> list[Materia]:
    return MateriaRepository(db).get_by_carrera(carrera_id)


def get_correlativas(db: Session, materia_id: int) -> list[Correlativa]:
    return CorrelativaRepository(db).get_by_materia(materia_id)


def get_materias_usuario(db: Session, usuario_id: int) -> list[MateriaUsuario]:
    return MateriaUsuarioRepository(db).get_by_usuario(usuario_id)


def add_materia_usuario(
    db: Session, datos: MateriaUsuarioCreate, usuario_id: int
) -> MateriaUsuario:
    if MateriaRepository(db).get_by_id(datos.materia_id) is None:
        raise MateriaNoEncontrada(f"No existe la materia {datos.materia_id}")

    repo = MateriaUsuarioRepository(db)
    if repo.get_by_usuario_y_materia(usuario_id, datos.materia_id) is not None:
        raise MateriaYaCargada("Esa materia ya está cargada")

    nueva = MateriaUsuario(usuario_id=usuario_id, **datos.model_dump())

    try:
        return repo.create(nueva)
    except IntegrityError:
        db.rollback()
        raise MateriaYaCargada("Esa materia ya está cargada")


def update_materia_usuario(
    db: Session,
    materia_usuario_id: int,
    usuario_id: int,
    datos: MateriaUsuarioUpdate,
) -> MateriaUsuario | None:
    return MateriaUsuarioRepository(db).update(materia_usuario_id, usuario_id, datos)


def delete_materia_usuario(
    db: Session, materia_usuario_id: int, usuario_id: int
) -> MateriaUsuario | None:
    return MateriaUsuarioRepository(db).delete(materia_usuario_id, usuario_id)


def calcular_promedio(db: Session, usuario_id: int) -> dict:
    cursadas = MateriaUsuarioRepository(db).get_by_usuario(usuario_id)
    computadas = [c for c in cursadas if c.nota_final is not None]

    if not computadas:
        return {"promedio": None, "materias_computadas": 0}

    promedio = sum(c.nota_final for c in computadas) / len(computadas)
    return {"promedio": round(promedio, 2), "materias_computadas": len(computadas)}