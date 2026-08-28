from sqlalchemy.orm import Session

from app.features.materias.model import Carrera, Correlativa, Materia, MateriaUsuario
from app.features.materias.schema import (
    CarreraCreate,
    CarreraUpdate,
    MateriaCreate,
    MateriaUpdate,
    MateriaUsuarioUpdate,
)


class CarreraRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Carrera]:
        return self.db.query(Carrera).all()

    def get_by_id(self, carrera_id: int) -> Carrera | None:
        return self.db.query(Carrera).filter(Carrera.id == carrera_id).first()

    def create(self, datos: CarreraCreate) -> Carrera:
        carrera = Carrera(**datos.model_dump())
        self.db.add(carrera)
        self.db.commit()
        self.db.refresh(carrera)
        return carrera

    def update(self, carrera_id: int, datos: CarreraUpdate) -> Carrera | None:
        carrera = self.get_by_id(carrera_id)
        if carrera is None:
            return None

        for campo, valor in datos.model_dump(exclude_unset=True).items():
            setattr(carrera, campo, valor)

        self.db.commit()
        self.db.refresh(carrera)
        return carrera

    def delete(self, carrera_id: int) -> Carrera | None:
        carrera = self.get_by_id(carrera_id)
        if carrera is None:
            return None

        self.db.delete(carrera)
        self.db.commit()
        return carrera


class MateriaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_carrera(self, carrera_id: int) -> list[Materia]:
        return (
            self.db.query(Materia)
            .filter(Materia.carrera_id == carrera_id)
            .order_by(Materia.anio, Materia.cuatrimestre)
            .all()
        )

    def get_by_id(self, materia_id: int) -> Materia | None:
        return self.db.query(Materia).filter(Materia.id == materia_id).first()

    def create(self, datos: MateriaCreate) -> Materia:
        materia = Materia(**datos.model_dump())
        self.db.add(materia)
        self.db.commit()
        self.db.refresh(materia)
        return materia

    def update(self, materia_id: int, datos: MateriaUpdate) -> Materia | None:
        materia = self.get_by_id(materia_id)
        if materia is None:
            return None

        for campo, valor in datos.model_dump(exclude_unset=True).items():
            setattr(materia, campo, valor)

        self.db.commit()
        self.db.refresh(materia)
        return materia

    def delete(self, materia_id: int) -> Materia | None:
        materia = self.get_by_id(materia_id)
        if materia is None:
            return None

        self.db.delete(materia)
        self.db.commit()
        return materia


class CorrelativaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_materia(self, materia_id: int) -> list[Correlativa]:
        return (
            self.db.query(Correlativa)
            .filter(Correlativa.materia_id == materia_id)
            .all()
        )


class MateriaUsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_usuario(self, usuario_id: int) -> list[MateriaUsuario]:
        return (
            self.db.query(MateriaUsuario)
            .filter(MateriaUsuario.usuario_id == usuario_id)
            .all()
        )

    def get_by_usuario_y_materia(
        self, usuario_id: int, materia_id: int
    ) -> MateriaUsuario | None:
        return (
            self.db.query(MateriaUsuario)
            .filter(
                MateriaUsuario.usuario_id == usuario_id,
                MateriaUsuario.materia_id == materia_id,
            )
            .first()
        )

    def get_by_id(
        self, materia_usuario_id: int, usuario_id: int
    ) -> MateriaUsuario | None:
        return (
            self.db.query(MateriaUsuario)
            .filter(
                MateriaUsuario.id == materia_usuario_id,
                MateriaUsuario.usuario_id == usuario_id,
            )
            .first()
        )

    def create(self, materia_usuario: MateriaUsuario) -> MateriaUsuario:
        self.db.add(materia_usuario)
        self.db.commit()
        self.db.refresh(materia_usuario)
        return materia_usuario

    def update(
        self,
        materia_usuario_id: int,
        usuario_id: int,
        datos: MateriaUsuarioUpdate,
    ) -> MateriaUsuario | None:
        materia_usuario = self.get_by_id(materia_usuario_id, usuario_id)
        if materia_usuario is None:
            return None

        for campo, valor in datos.model_dump(exclude_unset=True).items():
            setattr(materia_usuario, campo, valor)

        self.db.commit()
        self.db.refresh(materia_usuario)
        return materia_usuario

    def delete(
        self, materia_usuario_id: int, usuario_id: int
    ) -> MateriaUsuario | None:
        materia_usuario = self.get_by_id(materia_usuario_id, usuario_id)
        if materia_usuario is None:
            return None

        self.db.delete(materia_usuario)
        self.db.commit()
        return materia_usuario