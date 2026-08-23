from sqlalchemy.orm import Session
from app.features.materias.model import Carrera, Materia, MateriaUsuario, Correlativa
from app.features.materias.schema import MateriaUsuarioCreate, MateriaUsuarioUpdate

class CarreraRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(Carrera).all()

    def get_by_id(self, carrera_id: int):
        return self.db.query(Carrera).filter(Carrera.id == carrera_id).first()


class MateriaRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_carrera(self, carrera_id: int):
        return self.db.query(Materia).filter(Materia.carrera_id == carrera_id).all()

    def get_by_id(self, materia_id: int):
        return self.db.query(Materia).filter(Materia.id == materia_id).first()


class CorrelativaRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_materia(self, materia_id: int):
        return self.db.query(Correlativa).filter(
            Correlativa.materia_id == materia_id
        ).all()


class MateriaUsuarioRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_usuario(self, usuario_id: int):
        return self.db.query(MateriaUsuario).filter(
            MateriaUsuario.usuario_id == usuario_id
        ).all()

    def create(self, materia_usuario: MateriaUsuario):
        self.db.add(materia_usuario)
        self.db.commit()
        self.db.refresh(materia_usuario)
        return materia_usuario

    def update(self, materia_usuario_id: int, usuario_id: int, datos: MateriaUsuarioUpdate):
        materia_usuario = self.db.query(MateriaUsuario).filter(
            MateriaUsuario.id == materia_usuario_id,
            MateriaUsuario.usuario_id == usuario_id
        ).first()
        if materia_usuario:
            if datos.estado is not None:
                materia_usuario.estado = datos.estado
            if datos.nota_parcial_1 is not None:
                materia_usuario.nota_parcial_1 = datos.nota_parcial_1
            if datos.nota_parcial_2 is not None:
                materia_usuario.nota_parcial_2 = datos.nota_parcial_2
            if datos.nota_final is not None:
                materia_usuario.nota_final = datos.nota_final
            self.db.commit()
            self.db.refresh(materia_usuario)
        return materia_usuario

    def delete(self, materia_usuario_id: int, usuario_id: int):
        materia_usuario = self.db.query(MateriaUsuario).filter(
            MateriaUsuario.id == materia_usuario_id,
            MateriaUsuario.usuario_id == usuario_id
        ).first()
        if materia_usuario:
            self.db.delete(materia_usuario)
            self.db.commit()
        return materia_usuario