from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base
from app.features.materias.model import Materia, Carrera


class Recurso(Base):
    __tablename__ = "recursos"

    id = Column(Integer, primary_key=True, index=True)
    # Se agregó ForeignKey opcional hacia la tabla de usuarios
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    materia_id = Column(Integer, ForeignKey("materias.id"), nullable=False, index=True)
    titulo = Column(String(150), nullable=False)
    url = Column(Text, nullable=False)
    descripcion = Column(Text, nullable=False)
    tipo = Column(String, nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Convenio(Base):
    __tablename__ = "convenios"

    id = Column(Integer, primary_key=True, index=True)
    carrera_id = Column(Integer, ForeignKey("carreras.id"), nullable=False,  index=True)
    
    institucion = Column(String(150), nullable=False)
    carrera_destino = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=False)
    link_info = Column(Text, nullable=False)


class TalentoTech(Base):
    __tablename__ = "talentotech"

    id = Column(Integer, primary_key=True, index=True)
    carrera_id = Column(Integer, ForeignKey("carreras.id"), nullable=False, index=True)
    nombre_curso = Column(String(150), nullable=False)
    categoria = Column(String(20), nullable=False)
    descripcion = Column(Text, nullable=False)
    duracion = Column(String(50), nullable=False)
    link_inscripcion = Column(Text, nullable=False)