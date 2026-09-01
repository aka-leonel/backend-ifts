# backend-ifts
Backend para elproyecto integrador miIFTS

## Paginación

Los listados largos aceptan los query params `page` (default `1`) y `per_page`
(default `20`, máximo `100`) y devuelven un objeto envoltorio en vez de un
array plano:

```json
{
  "items": [ ... ],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "total_pages": 3
}
```

Endpoints paginados hoy:

- `GET /materias/carrera/{carrera_id}?page=1&per_page=10`
- `GET /recursos/?page=1&per_page=20`
- `GET /recursos/usuario/{usuario_id}?page=1&per_page=20`
- `GET /recursos/materia/{materia_id}?page=1&per_page=20`
- `GET /convenios/?page=1&per_page=20`
- `GET /talentotech/?page=1&per_page=20`
- `GET /recordatorios/?usuario_id=1&page=1&per_page=15`

Quedaron sin paginar a propósito los listados chicos y acotados (carreras,
correlativas de una materia, materias del usuario, y las variantes filtradas
por carrera/categoría de convenios y talentotech) porque no crecen lo
suficiente como para justificarlo.

El esquema (`PaginatedResponse`) y la dependencia (`PaginationParams`) están en
`app/shared/schemas/pagination.py` y `app/shared/utils/pagination.py`, listos
para reutilizar en cualquier endpoint nuevo con:

```python
from app.shared.schemas.pagination import PaginatedResponse
from app.shared.utils.pagination import PaginationParams, paginate

@router.get("/", response_model=PaginatedResponse[MiSchema])
def listar(pagination: PaginationParams = Depends(), db: Session = Depends(get_db)):
    query = db.query(MiModelo)  # o un query builder del repository
    return paginate(query, pagination)
```
