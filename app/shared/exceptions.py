"""Jerarquía única de excepciones de la API.

Todas heredan de `HTTPException`, así que FastAPI ya las serializa a
`{"detail": ...}` con su `status_code` y `headers`. Los services lanzan estas
excepciones y los routers no necesitan `try/except`: se propagan solas.
"""

from typing import Optional

from fastapi import HTTPException


class APIException(HTTPException):
    """Base de todas las excepciones de dominio de la API."""

    status_code: int = 400
    default_detail: str = "Solicitud inválida"

    def __init__(
        self,
        detail: Optional[str] = None,
        headers: Optional[dict] = None,
    ) -> None:
        super().__init__(
            status_code=self.status_code,
            detail=detail or self.default_detail,
            headers=headers,
        )


class BadRequestError(APIException):
    status_code = 400
    default_detail = "Solicitud inválida"


class UnauthorizedError(APIException):
    status_code = 401
    default_detail = "No autenticado"


class ForbiddenError(APIException):
    status_code = 403
    default_detail = "No tenés permiso para esta operación"


class NotFoundError(APIException):
    status_code = 404
    default_detail = "Recurso no encontrado"


class DuplicateError(APIException):
    status_code = 409
    default_detail = "El recurso ya existe"


class BusinessRuleError(APIException):
    status_code = 409
    default_detail = "Operación no permitida por una regla de negocio"


class DomainValidationError(APIException):
    status_code = 422
    default_detail = "Datos inválidos"
