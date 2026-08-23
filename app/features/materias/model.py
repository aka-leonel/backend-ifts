from sqlalchemy import Column, Integer, String, Float, ForeignKey
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
    carrera_id = Column(Integer, nullable=False)
    año = Column(Integer, nullable=False)
    cuatrimestre = Column(Integer, nullable=False)

class Correlativa(Base):
    __tablename__ = "correlativas"

    id = Column(Integer, primary_key=True, index=True)
    materia_id = Column(Integer, nullable=False)
    requiere_id = Column(Integer, nullable=False)

class MateriaUsuario(Base):
    __tablename__ = "materias_usuario"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=False)
    materia_id = Column(Integer, nullable=False)
    estado = Column(String, default="pendiente")
    nota_parcial_1 = Column(Float, nullable=True)
    nota_parcial_2 = Column(Float, nullable=True)
    nota_final = Column(Float, nullable=True)