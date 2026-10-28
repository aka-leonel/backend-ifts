from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator
from typing import Optional
from datetime import datetime

class RecursoBase(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=150)
    url: HttpUrl
    descripcion: str
    tipo: Optional[str] = None
    materia_id: int

    model_config = ConfigDict(from_attributes=True)

    @field_validator("titulo")
    @classmethod
    def _titulo_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El título no puede estar vacío")
        return v


class RecursoCreate(RecursoBase):
    pass    
    

class RecursoResponse(RecursoBase):
    id: int
    usuario_id: int
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)

class ConvenioCreate(BaseModel):
    institucion: str
    carrera_destino: str
    descripcion: str
    link_info: HttpUrl
    carrera_ids: Optional[list[int]] = None
    todas_las_carreras: bool = False

    @field_validator("institucion", "carrera_destino", "descripcion")
    @classmethod
    def _strip_textos(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v

class ConvenioUpdate(BaseModel):
    """Edición parcial: sólo se aplican los campos presentes en el body."""

    institucion: Optional[str] = None
    carrera_destino: Optional[str] = None
    descripcion: Optional[str] = None
    link_info: Optional[HttpUrl] = None
    carrera_ids: Optional[list[int]] = None
    todas_las_carreras: Optional[bool] = None

    @field_validator("institucion", "carrera_destino", "descripcion")
    @classmethod
    def _strip_textos(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v

class CarreraResumen(BaseModel):
    id: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)

class ConvenioResponse(BaseModel):
    """Contrato de salida: `carreras` es `[]` cuando `todas_las_carreras` es true."""

    id: int
    institucion: str
    carrera_destino: str
    descripcion: str
    link_info: str
    todas_las_carreras: bool
    carreras: list[CarreraResumen]

    model_config = ConfigDict(from_attributes=True)

class TalentoTechCreate(BaseModel):
    carrera_id: int
    nombre_curso: str
    categoria: str
    descripcion: str
    duracion: str
    link_inscripcion: HttpUrl

class TalentoTechResponse(TalentoTechCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)