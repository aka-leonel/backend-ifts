# backend-ifts

Backend para el proyecto integrador miIFTS.

## Autenticación y roles

La API usa JWT (Bearer token). Se obtiene con `POST /auth/login` (body JSON
`{email, password}`, lo usa el frontend) y se envía en el header
`Authorization: Bearer <token>` en los endpoints protegidos.

Para el botón **Authorize** de Swagger (`/docs`) hay un endpoint equivalente
`POST /auth/token` que acepta el formulario OAuth2 (campo *username* = email).

### Roles de usuario

El modelo `Usuario` tiene un campo `rol` con dos valores posibles:

| Rol          | Valor         | Descripción                                              |
|--------------|---------------|---------------------------------------------------------|
| Estudiante   | `estudiante`  | Rol por defecto al registrarse. Gestiona **sus propios** datos (cursadas, recursos, recordatorios). |
| Administrador| `admin`       | Además de lo anterior, gestiona el catálogo (carreras, materias, convenios, TalentoTech) y puede consultar las cursadas de cualquier alumno. |

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

| Endpoint                                             | Público | Estudiante | Admin |
|------------------------------------------------------|:-------:|:----------:|:-----:|
| `GET /materias/**` (carreras, materias, búsqueda, correlativas) |   ✅    |     ✅     |  ✅   |
| `POST/PUT/DELETE /materias/carreras/**`              |   ❌    |  ❌ (403)  |  ✅   |
| `POST/PUT/DELETE /materias/**` (materias)            |   ❌    |  ❌ (403)  |  ✅   |
| `GET/POST /materias/usuario/{id}`, `GET /materias/promedio/{id}` |   ❌    | ✅ solo propio | ✅ cualquiera |
| `PATCH/DELETE /materias/cursada/{id}`                |   ❌    | ✅ solo propio | ✅ solo propio |
| `GET /recursos/**`, `GET /convenios/**`, `GET /talentotech/**` |   ✅    |     ✅     |  ✅   |
| `POST /recursos/`                                    |   ❌    |     ✅     |  ✅   |
| `PUT/DELETE /recursos/{id}`                          |   ❌    | ✅ solo dueño | ✅ solo dueño |
| `POST/PUT/DELETE /convenios/**`, `.../talentotech/**`|   ❌    |  ❌ (403)  |  ✅   |
| `GET/POST /recordatorios/`, `DELETE /recordatorios/{id}` |   ❌    | ✅ solo propio | ✅ solo propio |

**Identidad:** los endpoints "propios" (cursadas, recordatorios) toman el
`usuario_id` **del token JWT**, no de la URL. En cursadas la URL todavía lleva
`{usuario_id}` y se valida contra el token: si no coincide y no sos admin → `403`.

**Ownership de recursos:** `PUT`/`DELETE` verifican `usuario_actual.id ==
recurso.usuario_id` → `403` si es de otro, `404` si no existe.

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
- `GET /recordatorios/?page=1&per_page=15` (del usuario del token)

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

## Validaciones y manejo de errores

### Jerarquía de excepciones (`app/shared/exceptions.py`)

Todos los services lanzan una de estas (heredan de `HTTPException`, así que se
propagan solas hasta la respuesta; los routers no hacen `try/except`):

| Excepción                | Código | Uso |
|--------------------------|:-----:|-----|
| `BadRequestError`        | 400 | Datos inválidos que no cubre Pydantic |
| `UnauthorizedError`      | 401 | Token ausente/ inválido, credenciales incorrectas |
| `ForbiddenError`         | 403 | Rol insuficiente, recurso de otro usuario |
| `NotFoundError`          | 404 | La entidad referida no existe |
| `DuplicateError`         | 409 | Único violado (código de materia, email, cursada repetida) |
| `BusinessRuleError`      | 409 | Regla de negocio (ver abajo) |
| `DomainValidationError`  | 422 | Validación de dominio fuera del schema |

Formato de respuesta de error (siempre): `{"detail": "<mensaje>"}`.
`app/main.py` registra además un handler de `IntegrityError` → 409 por si alguna
violación de integridad se escapa de los services.

### Validadores de schema (Pydantic `field_validator`)

- **Materia** (`MateriaCreate`/`Update`): `cuatrimestre` ∈ {1, 2}; `anio` ∈ [1, 6];
  `nombre` ≥ 2 caracteres; `codigo` no vacío (se normaliza a mayúsculas).
- **Carrera**: `duracion_cuatrimestres` ∈ [1, 12].
- **Cursada** (`MateriaUsuario*`): notas ∈ [1, 10].
- **Recordatorio**: `fecha` debe ser futura; `titulo`/`tipo` no vacíos.
- **Recurso**: `titulo` no vacío.
- **Usuario** (`UsuarioCreate`): `password` con al menos una letra y un número.

### Reglas de negocio (en los services)

- No se puede eliminar una **carrera** con materias asociadas → 409.
- No se puede eliminar una **materia** con cursadas asociadas → 409.
- Una cursada solo se crea si la **materia pertenece a la carrera del alumno** → 409.
- La fecha de un **recordatorio** debe ser futura → 422 (validador de schema).

## Tests

```bash
pip install -r requirements.txt
pytest -q
```

Los tests de autorización están en `tests/test_authorization.py` (roles admin vs
estudiante y ownership de recursos). Las validaciones y reglas de negocio están en
`tests/test_validaciones.py`. Los fixtures `auth_headers` (estudiante) y
`admin_headers` (admin) están en `tests/conftest.py`.
