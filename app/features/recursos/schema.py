from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional
from datetime import date, datetime

class RecursoBase(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=150)
    url: HttpUrl
    descripcion: str
    tipo: Optional[str] = None
    materia_id: int

    class Config:
        from_attributes = True

    @field_validator("titulo")
    @classmethod
    def _titulo_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El título no puede estar vacío")
        return v


class RecursoFilter(BaseModel):
    materia_id: Optional[int] = None
    tipo: Optional[str] = None
    desde: Optional[date] = None
    hasta: Optional[date] = None

    class Config:
        from_attributes = True

class RecursoCreate(RecursoBase):
    pass    
    

class RecursoResponse(RecursoBase):
    id: int
    usuario_id: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True

class ConvenioCreate(BaseModel):
    institucion: str
    carrera_destino: str
    descripcion: str
    link_info: HttpUrl
    carrera_id: int

class ConvenioResponse(ConvenioCreate):
    id: int

    class Config:
        from_attributes = True

class TalentoTechCreate(BaseModel):
    carrera_id: int
    nombre_curso: str
    categoria: str
    descripcion: str
    duracion: str
    link_inscripcion: HttpUrl

class TalentoTechResponse(TalentoTechCreate):
    id: int

    class Config:
        from_attributes = True