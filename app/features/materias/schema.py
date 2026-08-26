from pydantic import BaseModel, Field
from typing import Optional


NotaOpcional = Optional[float]


# ─── IFTS ────────────────────────────────────────────────────────────────────

class IFTSCreate(BaseModel):
    nombre: str
    ubicacion: Optional[str] = None


class IFTSResponse(BaseModel):
    id: int
    nombre: str
    ubicacion: Optional[str]

    class Config:
        from_attributes = True


# ─── Carrera ─────────────────────────────────────────────────────────────────

class CarreraCreate(BaseModel):
    nombre: str
    duracion_cuatrimestres: int
    ifts_id: int


class CarreraUpdate(BaseModel):
    nombre: Optional[str] = None
    duracion_cuatrimestres: Optional[int] = None


class CarreraResponse(BaseModel):
    id: int
    nombre: str
    duracion_cuatrimestres: int
    ifts_id: int

    class Config:
        from_attributes = True


class MateriaResponse(BaseModel):
    id: int
    nombre: str
    codigo: str
    carrera_id: int
    anio: int
    cuatrimestre: int

    class Config:
        from_attributes = True

class MateriaCreate(BaseModel):         
    carrera_id: int
    nombre: str
    codigo: str
    anio: int
    cuatrimestre: int

    class Config:
        from_attributes = True

class MateriaUpdate(BaseModel):         
    nombre: Optional[str] = None
    codigo: Optional[str] = None        
    anio: Optional[int] = None
    cuatrimestre: Optional[int] = None

class CorrelativaResponse(BaseModel):
    id: int
    materia_id: int
    requiere_id: int

    class Config:
        from_attributes = True


class MateriaUsuarioCreate(BaseModel):
    materia_id: int
    cursando: bool = False
    nota_parcial_1: NotaOpcional = Field(default=None, ge=1, le=10)
    nota_parcial_2: NotaOpcional = Field(default=None, ge=1, le=10)
    nota_final: NotaOpcional = Field(default=None, ge=1, le=10)


class MateriaUsuarioUpdate(BaseModel):
    cursando: Optional[bool] = None
    nota_parcial_1: NotaOpcional = Field(default=None, ge=1, le=10)
    nota_parcial_2: NotaOpcional = Field(default=None, ge=1, le=10)
    nota_final: NotaOpcional = Field(default=None, ge=1, le=10)


class MateriaUsuarioResponse(BaseModel):
    id: int
    usuario_id: int
    materia_id: int
    cursando: bool
    estado: str
    nota_parcial_1: NotaOpcional
    nota_parcial_2: NotaOpcional
    nota_final: NotaOpcional

    class Config:
        from_attributes = True


class PromedioResponse(BaseModel):
    promedio: Optional[float]
    materias_computadas: int