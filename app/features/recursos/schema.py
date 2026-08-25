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
    descripcion: str 
    link_info: HttpUrl 
    carrera_id: int

    class Config:
        from_attributes: True 

class ConvenioCreate(BaseModel):
    institucion = str
    carrera_destino = str
    descripcion: str 
    link_info: HttpUrl 
    carrera_id: int   


class TalentoTechResponse(BaseModel):
    id = int
    carrera_id = int 
    nombre_curso = str 
    categoria = str 
    descripcion = str 
    link_descripcion = HttpUrl
    duracion = str

    class Config:
        from_attributes = True
    