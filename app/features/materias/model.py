from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, UniqueConstraint
from app.database import Base


class Carrera(Base):
    __tablename__ = "carreras"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    duracion_cuatrimestres = Column(Integer, nullable=False)


class Materia(Base):
    __tablename__ = "materias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    carrera_id = Column(Integer, ForeignKey("carreras.id"), nullable=False, index=True)
    anio = Column(Integer, nullable=False)
    cuatrimestre = Column(Integer, nullable=False)


class Correlativa(Base):
    __tablename__ = "correlativas"
    __table_args__ = (
        UniqueConstraint("materia_id", "requiere_id", name="uq_correlativa"),
    )

    id = Column(Integer, primary_key=True, index=True)
    materia_id = Column(Integer, ForeignKey("materias.id"), nullable=False, index=True)
    requiere_id = Column(Integer, ForeignKey("materias.id"), nullable=False, index=True)


class MateriaUsuario(Base):
    __tablename__ = "materias_usuario"
    __table_args__ = (
        UniqueConstraint("usuario_id", "materia_id", name="uq_materia_por_usuario"),
    )

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    materia_id = Column(Integer, ForeignKey("materias.id"), nullable=False, index=True)
    cursando = Column(Boolean, nullable=False, default=False)
    nota_parcial_1 = Column(Float, nullable=True)
    nota_parcial_2 = Column(Float, nullable=True)
    nota_final = Column(Float, nullable=True)

    @property
    def estado(self) -> str:
        if self.cursando:
            return "cursando"
        if self.nota_final is not None:
            return "aprobada"
        return "pendiente"