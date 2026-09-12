from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional

class RecordatorioCreate(BaseModel):
    titulo: str = Field(..., examples=["Parcial de Programación I"])
    fecha: datetime = Field(
        ..., description="Datetime ISO 8601, tiene que ser futura",
        examples=["2026-12-15T10:00:00"],
    )
    tipo: str = Field(..., examples=["parcial"], description='Libre; convención: "parcial", "tp", "final", "otro"')
    materia_id: Optional[int] = Field(default=None, examples=[1])

    @field_validator("titulo", "tipo")
    @classmethod
    def _no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El campo no puede estar vacío")
        return v

    @field_validator("fecha")
    @classmethod
    def _fecha_futura(cls, v: datetime) -> datetime:
        ahora = datetime.now(tz=v.tzinfo) if v.tzinfo else datetime.now()
        if v < ahora:
            raise ValueError("La fecha del recordatorio debe ser futura")
        return v


class RecordatorioUpdate(BaseModel):
    """PATCH /recordatorios/{id} — edición parcial de un recordatorio propio.

    Todos los campos son opcionales; sólo se actualizan los que llegan en el
    body. Las mismas validaciones que en la creación aplican cuando el campo
    viene presente.
    """
    titulo: Optional[str] = Field(default=None, examples=["Parcial de Programación I"])
    fecha: Optional[datetime] = Field(
        default=None, description="Datetime ISO 8601, tiene que ser futura",
        examples=["2026-12-15T10:00:00"],
    )
    tipo: Optional[str] = Field(default=None, examples=["parcial"])
    materia_id: Optional[int] = Field(default=None, examples=[1])

    @field_validator("titulo", "tipo")
    @classmethod
    def _no_vacio(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("El campo no puede estar vacío")
        return v

    @field_validator("fecha")
    @classmethod
    def _fecha_futura(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return v
        ahora = datetime.now(tz=v.tzinfo) if v.tzinfo else datetime.now()
        if v < ahora:
            raise ValueError("La fecha del recordatorio debe ser futura")
        return v


class RecordatorioResponse(BaseModel):
    id: int
    titulo: str
    fecha: datetime
    tipo: str
    usuario_id: int
    materia_id: Optional[int]

    model_config = ConfigDict(from_attributes=True)
