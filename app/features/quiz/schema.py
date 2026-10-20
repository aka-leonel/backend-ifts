from typing import List

from pydantic import BaseModel, Field, model_validator


class Pregunta(BaseModel):
    enunciado: str
    opciones: List[str] = Field(..., min_length=4, max_length=4)
    correcta: int = Field(..., ge=0, le=3, description="Índice (0-3) de la opción correcta")
    explicacion: str = ""

    @model_validator(mode="after")
    def _opciones_validas(self) -> "Pregunta":
        if not self.enunciado.strip() or any(not o.strip() for o in self.opciones):
            raise ValueError("Pregunta con texto vacío")
        return self


class QuizResponse(BaseModel):
    preguntas: List[Pregunta]
