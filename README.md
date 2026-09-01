# backend-ifts

Backend para el proyecto integrador miIFTS.

## Autenticación y roles

La API usa JWT (Bearer token). Se obtiene con `POST /auth/login` y se envía en
el header `Authorization: Bearer <token>` en los endpoints protegidos.

### Roles de usuario

El modelo `Usuario` tiene un campo `rol` con dos valores posibles:

| Rol          | Valor         | Descripción                                              |
|--------------|---------------|---------------------------------------------------------|
| Estudiante   | `estudiante`  | Rol por defecto al registrarse. Gestiona sus propios datos (cursadas, recursos). |
| Administrador| `admin`       | Además de lo anterior, gestiona el catálogo académico (carreras y materias). |

**Alta de usuarios:** `POST /auth/registro` **siempre** crea usuarios con rol
`estudiante`. El campo `rol` del body se ignora (evita escalada de privilegios).
Los administradores se crean con `python seed.py` (`admin@miifts.ar` / `admin1234`)
o promoviendo un usuario en la base de datos.

### Dependencias de seguridad (`app/features/auth/dependencies.py`)

- `get_current_user` — valida el token y devuelve el usuario autenticado.
  Responde `401` si no hay token o es inválido.
- `require_admin` — además de autenticar, exige `rol == admin`.
  Responde `403` si el usuario es estudiante.

### Matriz de permisos

| Endpoint                                | Público | Estudiante | Admin |
|-----------------------------------------|:-------:|:----------:|:-----:|
| `GET /materias/**` (lecturas)           |   ✅    |     ✅     |  ✅   |
| `POST/PUT/DELETE /materias/carreras/**` |   ❌    |  ❌ (403)  |  ✅   |
| `POST/PUT/DELETE /materias/**` (materias)|  ❌    |  ❌ (403)  |  ✅   |
| `POST /recursos/`                       |   ❌    |     ✅     |  ✅   |
| `PUT /recursos/{id}`                    |   ❌    | ✅ solo dueño |  ✅ solo dueño |
| `DELETE /recursos/{id}`                 |   ❌    | ✅ solo dueño |  ✅ solo dueño |

**Recursos:** `PUT` y `DELETE` verifican que `usuario_actual.id == recurso.usuario_id`.
Si el recurso pertenece a otro usuario se responde `403`; si no existe, `404`.

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

## Tests

```bash
pip install -r requirements.txt
pytest -q
```

Los tests de autorización están en `tests/test_authorization.py` (roles admin vs
estudiante y ownership de recursos). Los fixtures `auth_headers` (estudiante) y
`admin_headers` (admin) están en `tests/conftest.py`.
