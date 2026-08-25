from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, UniqueConstraint
from app.database import Base
from app.features.materias.model import Materia, Carrera


class Recurso(Base):
    __tablename__ = "recursos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    materia_id = Column(Integer, nullable=False, ForeignKey("materias.id"), index=True)
    titulo = Column(String(150), nullable=False)
    url = Columnn(Text, nullable=False)
    descripcion = Column(Text, nullable=False)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)

class Convenio(Base):
    __tablename__ = "convenios"

    id = Column(Integer, primary_key=True, index=True)
    carrera_id = Column(Integer, nullable=False, ForeignKey("carreras.id"))
    institucion = Column(String(150), nullable=False)
    carrera_destino = Column(String(150), nullable=False)
    descripcioon = Column(Text, nullable=False)
    link_info = Column(Text, nullable=False)

class TalentoTech(Base):
    __table_name__ = "talentotech"

    id = Column(Integer, primary_key=True, index=True)
    carrera_id = Column(Integer, nullable=False, ForeignKey("carreras.id"))  
    nombre_curso = Column(String(150), nullable=False)
    categoria = Column(String(20), nullable=False)
    descripcion = Column(Text, nullable=False)
    duracion = Column(String(50), nullable=False)
    link_inscripcion = Column(Text, nullable=False)





