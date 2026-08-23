from pydantic import BaseModel
from typing import Optional

class CarreraResponse(BaseModel):
    id: int
    nombre: str
    duracion_cuatrimestres: int

    class Config:
        from_attributes = True

class MateriaResponse(BaseModel):
    id: int
    nombre: str
    carrera_id: int
    año: int
    cuatrimestre: int

    class Config:
        from_attributes = True

class CorrelativaResponse(BaseModel):
    id: int
    materia_id: int
    requiere_id: int

    class Config:
        from_attributes = True

class MateriaUsuarioCreate(BaseModel):
    materia_id: int
    estado: Optional[str] = "pendiente"
    nota_parcial_1: Optional[float] = None
    nota_parcial_2: Optional[float] = None
    nota_final: Optional[float] = None

class MateriaUsuarioUpdate(BaseModel):
    estado: Optional[str] = None
    nota_parcial_1: Optional[float] = None
    nota_parcial_2: Optional[float] = None
    nota_final: Optional[float] = None

class MateriaUsuarioResponse(BaseModel):
    id: int
    usuario_id: int
    materia_id: int
    estado: str
    nota_parcial_1: Optional[float]
    nota_parcial_2: Optional[float]
    nota_final: Optional[float]

    class Config:
        from_attributes = True