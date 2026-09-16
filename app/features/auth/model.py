from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
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
    apellido = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)  # hash, nunca texto plano
    carrera_id = Column(Integer, ForeignKey("carreras.id"), nullable=False, index=True)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    rol = Column(Enum(RolUsuario), nullable=False, default=RolUsuario.ESTUDIANTE)
    recordatorios = relationship("Recordatorio", back_populates="usuario")


class PasswordResetToken(Base):
    """Token de un solo uso para `POST /auth/reset-password`.

    Se guarda el hash (sha256) del token, nunca el token en texto plano —
    mismo criterio que `password_hash` para las contraseñas.
    """
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    expira = Column(DateTime(timezone=True), nullable=False)
    usado = Column(Boolean, nullable=False, default=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuario = relationship("Usuario")