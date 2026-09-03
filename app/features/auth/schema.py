from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
from enum import Enum

# Re-exportamos el enum para usarlo en los schemas
class RolUsuario(str, Enum):
    ESTUDIANTE = "estudiante"
    ADMIN = "admin"


# ========== Schemas de entrada (requests) ==========

class UsuarioCreate(BaseModel):
    """Datos necesarios para registrar un nuevo usuario.

    Nota de seguridad: el rol NO se acepta desde el request. El registro
    público siempre crea usuarios con rol `estudiante`; los administradores
    se crean por seed o promoción manual en la base de datos.
    """
    nombre: str = Field(
        ..., min_length=2, max_length=100, description="Nombre completo",
        examples=["Ada Lovelace"],
    )
    email: EmailStr = Field(
        ..., description="Correo electrónico único", examples=["ada@ifts.edu.ar"]
    )
    password: str = Field(
        ..., min_length=8,
        description="Contraseña en texto plano (mínimo 8 caracteres, al menos una letra y un número)",
        examples=["secreta123"],
    )
    carrera_id: int = Field(
        ..., description="ID de la carrera a la que pertenece", examples=[1]
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("La contraseña debe incluir al menos una letra y un número")
        return v

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        return v


class UsuarioLogin(BaseModel):
    """Datos necesarios para iniciar sesión."""
    email: EmailStr = Field(..., examples=["ada@ifts.edu.ar"])
    password: str = Field(..., examples=["secreta123"])


# ========== Schemas de salida (responses) ==========

class UsuarioResponse(BaseModel):
    """Datos del usuario que se devuelven al frontend (sin password_hash)."""
    id: int
    nombre: str
    email: str
    carrera_id: int
    fecha_registro: datetime
    rol: RolUsuario

    class Config:
        from_attributes = True  # Pydantic v2 (antes `orm_mode = True`)


class TokenResponse(BaseModel):
    """Respuesta del endpoint de login."""
    access_token: str
    token_type: str = "bearer"
    # Opcional: devolver también los datos del usuario en el mismo payload
    # para evitar un segundo viaje al frontend.
    usuario: Optional[UsuarioResponse] = None


class VerifyResponse(BaseModel):
    """Respuesta de `GET /auth/verify`."""
    valid: bool
    user_id: int


# ========== Schemas auxiliares (para cambiar datos) ==========

class UsuarioUpdate(BaseModel):
    """Para actualizar perfil (opcional, no urgente)."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    carrera_id: Optional[int] = None
    # No incluimos password aquí, eso iría en un endpoint aparte de cambio de contraseña