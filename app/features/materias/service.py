from sqlalchemy.orm import Session
from app.features.materias.repository import (
    CarreraRepository,
    MateriaRepository,
    CorrelativaRepository,
    MateriaUsuarioRepository
)
from app.features.materias.model import MateriaUsuario
from app.features.materias.schema import MateriaUsuarioCreate, MateriaUsuarioUpdate

def get_carreras(db: Session):
    repo = CarreraRepository(db)
    return repo.get_all()

def get_materias_by_carrera(db: Session, carrera_id: int):
    repo = MateriaRepository(db)
    return repo.get_by_carrera(carrera_id)

def get_correlativas(db: Session, materia_id: int):
    repo = CorrelativaRepository(db)
    return repo.get_by_materia(materia_id)

def get_materias_usuario(db: Session, usuario_id: int):
    repo = MateriaUsuarioRepository(db)
    return repo.get_by_usuario(usuario_id)

def add_materia_usuario(db: Session, datos: MateriaUsuarioCreate, usuario_id: int):
    repo = MateriaUsuarioRepository(db)
    nueva = MateriaUsuario(
        usuario_id=usuario_id,
        materia_id=datos.materia_id,
        estado=datos.estado,
        nota_parcial_1=datos.nota_parcial_1,
        nota_parcial_2=datos.nota_parcial_2,
        nota_final=datos.nota_final
    )
    return repo.create(nueva)

def update_materia_usuario(db: Session, materia_usuario_id: int, usuario_id: int, datos: MateriaUsuarioUpdate):
    repo = MateriaUsuarioRepository(db)
    return repo.update(materia_usuario_id, usuario_id, datos)

def delete_materia_usuario(db: Session, materia_usuario_id: int, usuario_id: int):
    repo = MateriaUsuarioRepository(db)
    return repo.delete(materia_usuario_id, usuario_id)

def calcular_promedio(db: Session, usuario_id: int):
    repo = MateriaUsuarioRepository(db)
    materias = repo.get_by_usuario(usuario_id)
    aprobadas = [m for m in materias if m.estado == "aprobada" and m.nota_final is not None]
    if not aprobadas:
        return 0.0
    promedio = sum(m.nota_final for m in aprobadas) / len(aprobadas)
    return round(promedio, 2)