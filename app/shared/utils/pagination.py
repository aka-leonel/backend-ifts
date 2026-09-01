from fastapi import Query
from sqlalchemy.orm import Query as SAQuery

from app.shared.schemas.pagination import PaginatedResponse


class PaginationParams:
    """Dependencia para leer ?page= y ?per_page= de la query string."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Número de página (empieza en 1)"),
        per_page: int = Query(
            20, ge=1, le=100, description="Elementos por página (máx. 100)"
        ),
    ):
        self.page = page
        self.per_page = per_page

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


def paginate(query: SAQuery, params: PaginationParams) -> PaginatedResponse:
    """Aplica offset/limit a un query de SQLAlchemy y arma la respuesta paginada."""
    total = query.count()
    items = query.offset(params.offset).limit(params.per_page).all()
    return PaginatedResponse.build(
        items=items, total=total, page=params.page, per_page=params.per_page
    )
