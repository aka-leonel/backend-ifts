from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional

class RecordatorioCreate(BaseModel):
    titulo: str
    fecha: datetime
    tipo: str
    materia_id: Optional[int] = None

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