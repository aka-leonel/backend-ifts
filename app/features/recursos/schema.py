from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime

class RecursoBase(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=150)
    url: HttpUrl
    descripcion: str
    materia_id: int

    class Config:
        from_attributes = True

class RecursoCreate(RecursoBase):
    usuario_id: int
    

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