from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
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
        ..., min_length=2, max_length=100, description="Nombre",
        examples=["Ada"],
    )
    apellido: str = Field(
        ..., min_length=2, max_length=100, description="Apellido",
        examples=["Lovelace"],
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

    @field_validator("nombre", "apellido")
    @classmethod
    def validate_nombre(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Debe tener al menos 2 caracteres")
        return v


class UsuarioLogin(BaseModel):
    """Datos necesarios para iniciar sesión."""
    email: EmailStr = Field(..., examples=["ada@ifts.edu.ar"])
    password: str = Field(..., examples=["secreta123"])


class ForgotPasswordRequest(BaseModel):
    """`POST /auth/forgot-password` — dispara el envío del email de reset."""
    email: EmailStr = Field(..., examples=["ada@ifts.edu.ar"])


class ResetPasswordRequest(BaseModel):
    """`POST /auth/reset-password` — token recibido por email + contraseña nueva.

    Misma validación de contraseña que `UsuarioCreate`.
    """
    token: str = Field(..., min_length=1, examples=["b8f2b3b7c1a94e6c9d0e..."])
    password: str = Field(
        ..., min_length=8,
        description="Contraseña nueva (mínimo 8 caracteres, al menos una letra y un número)",
        examples=["nuevaSecreta123"],
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("La contraseña debe incluir al menos una letra y un número")
        return v


# ========== Schemas de salida (responses) ==========

class UsuarioResponse(BaseModel):
    """Datos del usuario que se devuelven al frontend (sin password_hash)."""
    id: int
    nombre: str
    apellido: str
    email: str
    carrera_id: int
    fecha_registro: datetime
    rol: RolUsuario

    model_config = ConfigDict(from_attributes=True)  # antes `class Config: orm_mode`


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


class MensajeResponse(BaseModel):
    """Respuesta genérica de un solo mensaje (forgot/reset password)."""
    detail: str


# ========== Schemas auxiliares (para cambiar datos) ==========

class UsuarioUpdate(BaseModel):
    """Para actualizar perfil (opcional, no urgente)."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    carrera_id: Optional[int] = None
    # No incluimos password aquí, eso iría en un endpoint aparte de cambio de contraseña


class PerfilUpdate(BaseModel):
    """`PATCH /auth/me` — el alumno sólo edita su propio nombre y apellido.

    La carrera se muestra en el perfil pero no se cambia desde acá. El email
    identifica la cuenta y el rol nunca se acepta desde el request. Cualquier
    otro campo del body se ignora.
    """
    nombre: Optional[str] = Field(
        default=None, min_length=2, max_length=100, examples=["Ada"]
    )
    apellido: Optional[str] = Field(
        default=None, min_length=2, max_length=100, examples=["Lovelace"]
    )

    @field_validator("nombre", "apellido")
    @classmethod
    def _nombre_valido(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Debe tener al menos 2 caracteres")
        return v