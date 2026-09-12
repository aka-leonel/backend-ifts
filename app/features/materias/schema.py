from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional


NotaOpcional = Optional[float]


def _validar_nota(v: Optional[float]) -> Optional[float]:
    if v is not None and not (1 <= v <= 10):
        raise ValueError("La nota debe estar entre 1 y 10")
    return v


# ─── IFTS ────────────────────────────────────────────────────────────────────

class IFTSCreate(BaseModel):
    nombre: str
    ubicacion: Optional[str] = None


class IFTSResponse(BaseModel):
    id: int
    nombre: str
    ubicacion: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# ─── Carrera ─────────────────────────────────────────────────────────────────

class CarreraCreate(BaseModel):
    nombre: str
    duracion_cuatrimestres: int
    ifts_id: int

    @field_validator("nombre")
    @classmethod
    def _nombre_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        return v

    @field_validator("duracion_cuatrimestres")
    @classmethod
    def _duracion_valida(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 12):
            raise ValueError("La duración debe estar entre 1 y 12 cuatrimestres")
        return v


class CarreraUpdate(BaseModel):
    nombre: Optional[str] = None
    duracion_cuatrimestres: Optional[int] = None

    @field_validator("nombre")
    @classmethod
    def _nombre_no_vacio(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        return v

    @field_validator("duracion_cuatrimestres")
    @classmethod
    def _duracion_valida(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 12):
            raise ValueError("La duración debe estar entre 1 y 12 cuatrimestres")
        return v


class CarreraResponse(BaseModel):
    id: int
    nombre: str
    duracion_cuatrimestres: int
    ifts_id: int

    model_config = ConfigDict(from_attributes=True)


class MateriaResponse(BaseModel):
    id: int
    nombre: str
    codigo: str
    carrera_id: int
    anio: int
    cuatrimestre: int

    model_config = ConfigDict(from_attributes=True)


class MateriaCreate(BaseModel):
    carrera_id: int
    nombre: str
    codigo: str
    anio: int
    cuatrimestre: int

    model_config = ConfigDict(from_attributes=True)

    @field_validator("nombre")
    @classmethod
    def _nombre_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        return v

    @field_validator("codigo")
    @classmethod
    def _codigo_no_vacio(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("El código no puede estar vacío")
        return v

    @field_validator("anio")
    @classmethod
    def _anio_valido(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 6):
            raise ValueError("El año debe estar entre 1 y 6")
        return v

    @field_validator("cuatrimestre")
    @classmethod
    def _cuatrimestre_valido(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in (1, 2):
            raise ValueError("El cuatrimestre debe ser 1 o 2")
        return v


class MateriaUpdate(BaseModel):
    nombre: Optional[str] = None
    codigo: Optional[str] = None
    anio: Optional[int] = None
    cuatrimestre: Optional[int] = None

    @field_validator("nombre")
    @classmethod
    def _nombre_no_vacio(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        return v

    @field_validator("codigo")
    @classmethod
    def _codigo_no_vacio(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper()
        if not v:
            raise ValueError("El código no puede estar vacío")
        return v

    @field_validator("anio")
    @classmethod
    def _anio_valido(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 6):
            raise ValueError("El año debe estar entre 1 y 6")
        return v

    @field_validator("cuatrimestre")
    @classmethod
    def _cuatrimestre_valido(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in (1, 2):
            raise ValueError("El cuatrimestre debe ser 1 o 2")
        return v


class CorrelativaResponse(BaseModel):
    id: int
    materia_id: int
    requiere_id: int
    requiere: Optional[MateriaResponse] = None

    model_config = ConfigDict(from_attributes=True)


class MateriaUsuarioCreate(BaseModel):
    materia_id: int = Field(..., examples=[1])
    cursando: bool = Field(default=False, examples=[True])
    nota_parcial_1: NotaOpcional = Field(default=None, ge=1, le=10, examples=[8])
    nota_parcial_2: NotaOpcional = Field(default=None, ge=1, le=10, examples=[7])
    examen_final: NotaOpcional = Field(
        default=None, ge=1, le=10, examples=[None],
        description="Nota del examen final rendido. No aplica si promocionó (parciales >= 7): en ese caso se ignora.",
    )

    @field_validator("nota_parcial_1", "nota_parcial_2", "examen_final")
    @classmethod
    def _notas_en_rango(cls, v: NotaOpcional) -> NotaOpcional:
        return _validar_nota(v)


class MateriaUsuarioUpdate(BaseModel):
    cursando: Optional[bool] = None
    nota_parcial_1: NotaOpcional = Field(default=None, ge=1, le=10)
    nota_parcial_2: NotaOpcional = Field(default=None, ge=1, le=10)
    examen_final: NotaOpcional = Field(default=None, ge=1, le=10)

    @field_validator("nota_parcial_1", "nota_parcial_2", "examen_final")
    @classmethod
    def _notas_en_rango(cls, v: NotaOpcional) -> NotaOpcional:
        return _validar_nota(v)


class MateriaUsuarioResponse(BaseModel):
    id: int
    usuario_id: int
    materia_id: int
    cursando: bool
    estado: str
    nota_parcial_1: NotaOpcional
    nota_parcial_2: NotaOpcional
    examen_final: NotaOpcional
    nota_final: NotaOpcional = Field(
        description="Nota que cierra la cursada: promedio de los parciales si "
        "promocionó, o el examen_final rendido si no. Es un valor calculado, "
        "no se manda en el request."
    )

    model_config = ConfigDict(from_attributes=True)


class PromedioResponse(BaseModel):
    promedio: Optional[float]
    materias_computadas: int
