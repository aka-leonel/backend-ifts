from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

# Definimos el rol como un Enum de Python (opcional pero recomendado)
class RolUsuario(str, enum.Enum):
    ESTUDIANTE = "estudiante"
    ADMIN = "admin"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)  # hash, nunca texto plano
    carrera_id = Column(Integer, ForeignKey("carreras.id"), nullable=False, index=True)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    rol = Column(Enum(RolUsuario), nullable=False, default=RolUsuario.ESTUDIANTE)