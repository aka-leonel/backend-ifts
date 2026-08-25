from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class RecursoBase(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=150)
    url: HttpUrl
    descripcion: str | None = None
    materia_id = int

    class Config:
        from_attributes = True


class RecursoCreate(BaseModel):
    pass

class RecursoResponse(BaseModel):
    id = int
    usuario_id = int
    fecha_creacion = datetime

    class Config:
        from_attributes = True


class ConvenioResponse(BaseModel):
    id = int
    institucion = str
    carrera_destino = str
    descripcion: str | None = None
    link_info: HttpUrl 
    carrera_id: int

    class Config:
        from_attributes: True 

class TalentoTechResponse(BaseModel):
    id = int
    carrera_id = int | None = None
    nombre_curso = str | None = None
    categoria = str | None = None
    descripcion = str | None = None
    link_descripcion = HttpUrl | None = None
    duracion = str | None = None

    class Config:
        from_attributes = True
    