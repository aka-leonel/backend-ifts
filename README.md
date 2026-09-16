# backend-ifts

Backend para el proyecto integrador miIFTS.

## Cómo levantar el proyecto

Primero, en ambos casos: `cp .env.example .env` (o copiarlo a mano en Windows)
y ajustar `SECRET_KEY` si hace falta.

### Local (SQLite, sin Docker)

El proyecto usa **Python 3.12** (ver `.python-version`, mismo que CI y Docker).
Si tenés varias versiones instaladas, creá el venv apuntando a esa:

```bash
py -3.12 -m venv venv          # Windows (o "python3.12 -m venv venv" en Mac/Linux)
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
python seed.py                 # crea las tablas y carga datos de referencia
uvicorn app.main:app --reload
```

Swagger en `http://localhost:8000/docs`. Credenciales de prueba:
`test@miifts.ar` / `test1234`.

Este flujo no usa Alembic — `seed.py` crea el esquema directamente contra la
SQLite local, como siempre. Alembic entra en juego cuando se quiere migrar un
esquema existente sin perder datos (ver más abajo) o al correr contra Postgres.

### Docker (Postgres)

```bash
docker compose up --build
```

Levanta Postgres + la API. El contenedor de la API corre `alembic upgrade head`
automáticamente antes de arrancar `uvicorn`, así que el esquema siempre queda
al día. API en `http://localhost:8000`, Postgres en el puerto 5432 del host.

Para reiniciar con una base limpia: `docker compose down -v` (el `-v` borra el
volumen de Postgres).

## Migraciones con Alembic

El esquema de la base se versiona con [Alembic](https://alembic.sqlalchemy.org/).
Cada cambio en un `model.py` necesita su propia migración.

| Acción | Comando |
|--------|---------|
| Generar una migración a partir de los cambios en los modelos | `alembic revision --autogenerate -m "descripción corta"` |
| Aplicar todas las migraciones pendientes | `alembic upgrade head` |
| Deshacer la última migración | `alembic downgrade -1` |
| Ver el historial | `alembic history` |

Flujo típico al cambiar un modelo:

1. Editar el `model.py` correspondiente (agregar columna, tabla, etc.).
2. `alembic revision --autogenerate -m "agrega X a Y"` — revisar el archivo
   generado en `alembic/versions/` (el autogenerate no detecta todo, por
   ejemplo renombres de columna).
3. `alembic upgrade head` para aplicarlo a tu DB local y confirmar que anda.
4. Commitear el archivo de migración junto con el cambio del modelo.

**Migraciones en paralelo:** si dos personas generan una migración cada una
desde el mismo estado (`head`) en ramas distintas, al mergear las dos quedan
dos "heads" en `alembic/versions/`. Se resuelve con `alembic merge heads -m
"merge"` (crea una migración que une ambas), o borrando y regenerando la
migración propia contra el `head` ya actualizado después del merge.

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

## Estructura de respuestas

Contrato único para el front:

| Tipo de respuesta | Forma | Cuándo |
|-------------------|-------|--------|
| **Colección** | `{ "items": [...], "total", "page", "per_page", "total_pages" }` | **todos** los `GET` que devuelven una lista |
| **Recurso** | objeto plano con sus campos | `GET`/`POST`/`PUT`/`PATCH` de un ítem |
| **Sin contenido** | `204`, body vacío | **todos** los `DELETE` |
| **Error** | `{ "detail": "<string>" }` (+ `errors` en los `422`) | ver *Validaciones y manejo de errores* |

### Paginación

**Todos** los listados aceptan `page` (default `1`) y `per_page` (default `20`,
máximo `100`) y devuelven el envoltorio `PaginatedResponse`:

```json
{ "items": [ ... ], "total": 42, "page": 1, "per_page": 20, "total_pages": 3 }
```

Alcanza a: `/materias/carreras`, `/materias/carrera/{id}`, `/materias/buscar`,
`/materias/correlativas/{id}`, `/materias/usuario/{id}`, `/recordatorios/`,
`/recursos/` y `/recursos/usuario|materia/{id}`, `/convenios/` y
`/convenios/carrera/{id}`, `/talentotech/` y `/talentotech/carrera|categoria/{x}`.

`GET /materias/correlativas/{id}` embebe además la materia correlativa completa
en el campo `requiere` de cada item.

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

**Formato de respuesta de error — unificado en toda la API:** `detail` es
**siempre un string**.

```json
{ "detail": "No se encontró el recurso 99999" }
```

Los errores de validación (`422`) agregan además el desglose campo por campo,
útil para marcar los inputs en un formulario:

```json
{
  "detail": "El cuatrimestre debe ser 1 o 2",
  "errors": [
    { "campo": "cuatrimestre", "msg": "El cuatrimestre debe ser 1 o 2" },
    { "campo": "codigo", "msg": "El código no puede estar vacío" }
  ]
}
```

`app/main.py` registra los handlers globales: `APIException` (nuestra jerarquía),
`RequestValidationError` (normaliza los 422 de Pydantic al formato de arriba) e
`IntegrityError` → 409 por si alguna violación de integridad se escapa de los
services.

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
