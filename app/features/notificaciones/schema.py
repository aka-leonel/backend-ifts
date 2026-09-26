from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator
from datetime import datetime


class PushSubscriptionCreate(BaseModel):
    """Datos para crear una suscripción push (POST /notificaciones/suscripcion).

    endpoint: URL del endpoint de push del navegador (validada como HttpUrl).
    p256dh: Clave pública P-256 en base64 URL-safe (mínimo 88 caracteres).
    auth: Secreto de autenticación en base64 URL-safe (mínimo 24 caracteres).
    """
    endpoint: HttpUrl = Field(..., description="URL del endpoint de push del navegador")
    p256dh: str = Field(..., min_length=87, description="Clave pública P-256 (base64 URL-safe)")
    auth: str = Field(..., min_length=24, description="Secreto de autenticación (base64 URL-safe)")

    @field_validator("p256dh", "auth")
    @classmethod
    def _no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El campo no puede estar vacío")
        return v


class PushSubscriptionDelete(BaseModel):
    """Datos para eliminar una suscripción push (DELETE /notificaciones/suscripcion).

    Se identifica la suscripción a eliminar por su endpoint.
    """
    endpoint: str = Field(..., min_length=1, description="URL del endpoint de la suscripción a eliminar")

    @field_validator("endpoint")
    @classmethod
    def _no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El endpoint no puede estar vacío")
        return v


class PushSubscriptionResponse(BaseModel):
    """Respuesta con los datos de una suscripción push.

    Incluye las claves para que el frontend pueda gestionarlas si es necesario.
    """
    id: int
    usuario_id: int
    endpoint: str
    p256dh: str
    auth: str
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)