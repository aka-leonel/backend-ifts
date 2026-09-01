from datetime import datetime, date
from pydantic import BaseModel, field_validator
from typing import Optional

class RecordatorioCreate(BaseModel):
    titulo: str
    fecha: datetime
    tipo: str
    materia_id: Optional[int] = None

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

class RecordatorioResponse(BaseModel):
    id: int
    titulo: str
    fecha: datetime
    tipo: str
    usuario_id: int
    materia_id: Optional[int]

    class Config:
        from_attributes = True

class RecordatorioFilter(BaseModel):
    tipo: Optional[str] = None
    desde: Optional[date] = None
    hasta: Optional[date] = None
    materia_id: Optional[int] = None

    class Config:
        from_attributes = True
