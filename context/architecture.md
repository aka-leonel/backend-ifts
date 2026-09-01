# Arquitectura del Proyecto miIFTS

## Stack Tecnológico
| Componente | Tecnología | Versión |
|------------|-----------|---------|
| Framework web | FastAPI | 0.115.5 |
| Servidor ASGI | Uvicorn | 0.32.1 |
| ORM | SQLAlchemy | 2.0.36 |
| Migraciones | Alembic | 1.14.0 |
| Base de datos | SQLite (default) / PostgreSQL | — |
| Validación de schemas | Pydantic v2 | — |
| Autenticación JWT | python-jose | 3.3.0 |
| Hashing de contraseñas | passlib + bcrypt | 1.7.4 / 4.0.1 |
| Variables de entorno | python-dotenv | 1.0.1 |
| Testing | pytest + pytest-cov | 8.3.3 / 5.0.0 |
| Code quality | black + pylint | 24.8.0 / 3.2.7 |
| CORS | fastapi.middleware.cors | — |

## Estructura de Directorios
```
app/
├── main.py              # Entry point: FastAPI app, routers, CORS, health
├── database.py          # SQLAlchemy engine, SessionLocal, Base, get_db()
├── features/
│   ├── auth/
│   │   ├── model.py     # Usuario, RolUsuario (SQLAlchemy)
│   │   ├── schema.py    # UsuarioCreate/Login/Response, TokenResponse (Pydantic)
│   │   ├── repository.py # AuthRepository (CRUD)
│   │   ├── service.py   # AuthService (registro, login, JWT)
│   │   ├── router.py    # /auth/* endpoints
│   │   ├── dependencies.py # get_current_user (OAuth2 + JWT)
│   │   └── __init__.py  # vacío
│   ├── materias/
│   │   ├── model.py     # IFTS, Carrera, Materia, Correlativa, MateriaUsuario
│   │   ├── schema.py    # CarreraCreate/Update, MateriaCreate/Update, MateriaUsuario, PromedioResponse
│   │   ├── repository.py # CarreraRepository, CorrelativaRepository, MateriaRepository, MateriaUsuarioRepository
│   │   ├── service.py   # funciones de servicio (CRUD + promedio + cursadas)
│   │   ├── router.py    # /materias/* endpoints
│   │   └── __init__.py  # vacío
│   ├── recordatorios/
│   │   ├── model.py     # Recordatorio
│   │   ├── schema.py    # RecordatorioCreate, RecordatorioResponse
│   │   ├── repository.py # RecordatorioRepository
│   │   ├── service.py   # get/create/delete recordatorios
│   │   ├── router.py    # /recordatorios/* endpoints
│   │   └── __init__.py  # vacío
│   ├── recursos/
│   │   ├── model.py     # Recurso, Convenio, TalentoTech
│   │   ├── schema.py    # RecursoCreate/Response, ConvenioCreate/Response, TalentoTechCreate/Response
│   │   ├── repository.py # RecursoRepository, ConvenioRepository, TalentoTechRepository
│   │   ├── service.py   # RecursoService, ConvenioService, TalentoTechService
│   │   ├── router.py    # redirige a sub-routers
│   │   ├── dependencies.py # get_recurso/convenio/talentotech_service
│   │   ├── routers/
│   │   │   ├── recursos.py    # /recursos/*
│   │   │   ├── convenios.py   # /convenios/*
│   │   │   └── talentotech.py # /talentotech/*
│   │   └── __init__.py  # exports de schemas
│   └── shared/
│       ├── models/      # .gitkeep (sin modelos compartidos actuales)
│       ├── schemas/     # .gitkeep (sin schemas compartidos actuales)
│       └── utils/       # .gitkeep (sin utilidades compartidas actuales)
└── seed.py              # Script de seed de base de datos
```

## Patrón Arquitectónico por Feature
Cada feature sigue un patrón de 4 capas:
1. **model.py** — Modelos SQLAlchemy (tablas, relaciones, constraints).
2. **schema.py** — Schemas Pydantic (entrada/salida, validación).
3. **repository.py** — Capa de acceso a datos (consultas SQLAlchemy, CRUD).
4. **service.py** — Lógica de negocio (orquesta repository, levanta excepciones).
5. **router.py** — Endpoints FastAPI (dependencias, status codes, response_model).

Flujo de una request: `Router → Service → Repository → DB`.

## Modelos de Base de Datos
| Tabla | PK | FKs clave | Observaciones |
|-------|----|-----------|---------------|
| `users` | id | carrera_id → carreras | email único, password_hash, rol (enum) |
| `carreras` | id | ifts_id → ifts | nombre, duración_cuatrimestres |
| `ifts` | id | — | Nombre de institución, ubicación |
| `materias` | id | carrera_id → carreras | código único por carrera (UniqueConstraint) |
| `correlativas` | id | materia_id → materias, requiere_id → materias | prerequisito de materia |
| `materias_usuario` | id | usuario_id → users, materia_id → materias | cursando, notas (parcial 1/2, final), estado calculado |
| `recordatorios` | id | usuario_id → users, materia_id → materias (opt.) | título, fecha, tipo |
| `recursos` | id | usuario_id → users, materia_id → materias | título, URL, descripción, fecha_creacion |
| `convenios` | id | carrera_id → carreras | institución, carrera_destino, link_info |
| `talentotech` | id | carrera_id → carreras | nombre_curso, categoría, link_inscripcion |

## Configuración
- **`.env`** (gitignored): `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`.
- **`DATABASE_URL`**: default `sqlite:///./miifts.db`.
- **`SECRET_KEY`**: default fallback `"mi-secret-key-muy-seguro-cambiar-en-produccion"` (JWT HS256).
- **`CORS_ORIGINS`**: default `http://localhost:5173,http://127.0.0.1:5173`.

## Integraciones
- **JWT**: `python-jose` con HS256, expiry 24h, payload con `sub` (user_id) y `email`.
- **OAuth2**: `OAuth2PasswordBearer` con `tokenUrl="/auth/login"`.
- **CORS**: Middleware de FastAPI con orígenes configurables.
- **Alembic**: Configurado para migraciones (presente en dependencias).

## Testing
- Base de datos SQLite en memoria (`sqlite:///:memory:`) con `StaticPool`.
- `TestClient` de FastAPI con `dependency_overrides` para `get_db`.
- Fixtures en `tests/conftest.py`: `client`, `db_session`, `carrera_test`, `usuario_payload`, `usuario_registrado`, `auth_headers`.
- Tests en `tests/test_auth.py` y `tests/test_materias.py`.
- `test_api.py` como script de prueba manual (no pytest).
- `api-requests.http` como colección de requests para cliente HTTP.

## Convenciones
- `from_attributes = True` en Pydantic (v2) para compatibilidad con SQLAlchemy.
- Nombres de tablas snake_case explícitos.
- Excepciones personalizadas de servicio (ej: `RecursoNotFound`, `ConvenioNotFound`).
- Los routers devuelven `response_model` explícito y status codes HTTP.
- `seed.py` drop+create tables y llena datos de IFTS/carreras/materias.