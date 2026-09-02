# miIFTS — Backend MVP

## Qué es

API REST para que un estudiante del IFTS lleve el seguimiento de su carrera:
consultar el plan de estudios, registrar sus cursadas y notas, guardar material
de estudio y anotar fechas de parciales/finales. Incluye un rol **admin** que
administra el catálogo académico.

## Stack

FastAPI + SQLAlchemy + SQLite. Auth con JWT (HS256, 24 h). Passwords con bcrypt.
Arquitectura por capas y por feature: `router → service → repository → model`,
con `app/shared/` para paginación y jerarquía de errores. Swagger en `/docs`.

## Funcionalidades

### Autenticación y roles
- Registro (siempre rol `estudiante`; el rol del body se ignora → sin escalada de
  privilegios), login (JSON para el front, form OAuth2 para Swagger),
  `/auth/me`, `/auth/verify`.
- Dos roles: `estudiante` y `admin`. Dependencias `get_current_user` (401) y
  `require_admin` (403).

### Catálogo académico (`/materias`)
- Estructura: IFTS → Carrera → Materia → Correlativas.
- Lectura pública: listar carreras, materias por carrera (paginado), búsqueda por
  nombre/código con filtros de año y cuatrimestre, correlativas (con la materia
  correlativa embebida en `requiere`).
- Escritura (carreras y materias): solo admin. Con validaciones (año 1–6,
  cuatrimestre 1/2, duración 1–12) y reglas de negocio (no borrar carrera con
  materias, no borrar materia con cursadas, código de materia único por
  carrera → 409).

### Cursadas y promedio (`/materias/usuario`, `/materias/cursada`, `/materias/promedio`)
- El alumno registra las materias que cursa/aprobó, con notas parciales y final
  (1–10).
- Regla: solo se puede cargar una materia de la carrera del alumno. Cálculo de
  promedio sobre notas finales.

### Recursos de estudio (`/recursos`, `/convenios`, `/talentotech`)
- Recursos: links de material por materia, con dueño. Lectura pública con filtros
  (materia, tipo, rango de fechas) y paginación. Crear requiere login;
  editar/borrar solo el dueño (403 si no).
- Convenios y cursos TalentoTech: lectura pública; alta/edición/baja solo admin.

### Recordatorios (`/recordatorios`)
- Agenda de fechas (parcial/tp/final/otro) del alumno. Listado paginado con
  filtros por tipo, materia y rango de fechas. Validación de fecha futura (422).

## Contrato de respuestas (para el front)

| Respuesta | Forma |
|-----------|-------|
| Colección (todo GET de lista) | `{ items, total, page, per_page, total_pages }` |
| Recurso (GET/POST/PUT/PATCH de un ítem) | objeto plano |
| DELETE | `204` sin body |
| Error | `{ "detail": "<string>" }` — los `422` agregan `errors: [{campo, msg}]` |

Detalle en `README.md` → *Estructura de respuestas* y *Validaciones y manejo de
errores*.

---

## Límites del MVP (fuera de alcance por ahora)

- **Sin persistencia gestionada**: corre sobre SQLite local. No hay migraciones
  (el schema se crea con `Base.metadata.create_all()` al arrancar).
- **Sin deploy**: no hay Dockerfile ni hosting; la API solo corre en la máquina
  del dev.
- **Identidad parcial desde el token** (ver *Deuda técnica* #1): varios endpoints
  de cursadas y recordatorios reciben `usuario_id` por path/query y **no** lo
  validan contra el JWT. El "un alumno solo ve lo suyo (403)" está implementado
  para **recursos**, no para cursadas ni recordatorios.
- **Sin recuperación de contraseña, refresh token ni logout real** (JWT stateless).
- **Recursos = solo links**: no hay carga de archivos.
- **Sin notificaciones** de recordatorios (no se envían mails ni push).
- **Sin endpoints de detalle**: no existe `GET /materias/{id}` ni
  `GET /materias/carreras/{id}` individuales; el front resuelve por las listas.
- **Admin se crea solo por seed o a mano en la DB**.
- **Un IFTS**: el modelo soporta varios, el seed carga uno.

---

## Deuda técnica / pendientes

| # | Tema | Detalle | Dónde |
|---|------|---------|-------|
| 1 | **Identidad desde el token** | `usuario_id` viene del path/query en cursadas, promedio y recordatorios. `get_usuario_actual()` está hardcodeado a `1`. Falta `Depends(get_current_user)` + 403 si el `usuario_id` pedido no es el propio (salvo admin). | `materias/router.py`, `recordatorios/router.py` |
| 2 | **Base de datos local** | SQLite + `create_all()`. Sin Alembic (está en `requirements.txt` sin usar). `psycopg2-binary` comentado. | `app/database.py`, `app/main.py` |
| 3 | **Sin deploy** | Falta Dockerfile, hosting, `.env.example`, branch protection en `dev`/`main`. `SECRET_KEY` tiene default hardcodeado. | raíz, `auth/service.py` |
| 4 | **Contrato para el front** | Faltan endpoints de detalle. `api-requests.http` desactualizado. CORS default solo localhost:5173. Sin doc de integración. | varios |
| 5 | **Deuda de calidad** | `class Config` de Pydantic v2 deprecado (~15 warnings). `black` sin correr (32 archivos) y sin gate en CI. Python 3.14 local vs 3.12 CI. `datetime.utcnow()` deprecado en `auth/service.py` y `jose`. `python-jose` 3.3.0 (2021, poco mantenido). Imports muertos (`get_current_user` en `recursos/schema.py`; schemas `*Filter` no usados). Coverage bajo en repos de recursos (28–50%). | schemas, workflow, `auth/service.py` |

Estado de tests: **60 pasando**, coverage **~81%**.

---

## Cómo avanzar con el front (dentro de los límites del MVP)

1. **Fuente de verdad = OpenAPI.** El backend expone el schema en
   `GET /openapi.json` y Swagger en `/docs`. Generar un cliente tipado con
   `openapi-typescript` (tipos) u `orval` / `openapi-generator` (cliente + hooks).
2. **Auth flow:**
   - `POST /auth/login` con `{ email, password }` → `{ access_token, token_type, usuario }`.
   - Guardar el token (memoria + `localStorage` o cookie) y mandarlo en
     `Authorization: Bearer <token>` en cada request.
   - Interceptar `401` → limpiar sesión y mandar a login. `403` → “no tenés permiso”.
3. **Manejo de respuestas** (contrato ya unificado):
   - Listas: siempre `res.items` + `res.total` / `res.total_pages` para paginar.
   - Errores: mostrar `res.detail` (string). En formularios, usar `res.errors`
     (`[{campo, msg}]`) para marcar campos.
4. **Pantallas MVP sugeridas:**
   - Registro / login.
   - Plan de estudios: carreras → materias por carrera → correlativas.
   - Mis cursadas: alta de cursada, notas, promedio.
   - Recursos: lista con filtros + alta (requiere login), editar/borrar solo propios.
   - Recordatorios: agenda con filtros, alta con fecha futura.
5. **Stack sugerido** (o el que maneje el equipo): Vite + React + TanStack Query
   + cliente generado. Nada acoplado al backend salvo el `baseURL`.
6. **Requisitos del backend para poder integrar** (van al Sprint 2):
   - Agregar el origin del front a `CORS_ORIGINS`.
   - Endpoints de detalle `GET /materias/{id}` y `GET /materias/carreras/{id}`.
   - Cerrar la brecha de identidad (#1) para que “mis cursadas / mis recordatorios”
     sean realmente del usuario logueado.

---

## Cómo sacar la BD de local

`app/database.py` **ya** lee `DATABASE_URL` de entorno (SQLite es solo el
fallback), así que el cambio es acotado:

1. **Proveedor gestionado free tier:** Neon, Supabase o Railway (Postgres).
   Crear la base y copiar la `DATABASE_URL` (`postgresql+psycopg://user:pass@host/db`).
2. **Driver:** descomentar/actualizar en `requirements.txt` → `psycopg[binary]`
   (o `psycopg2-binary`).
3. **Migraciones con Alembic** (reemplaza `Base.metadata.create_all()`):
   - `alembic init alembic`, apuntar `sqlalchemy.url` a `DATABASE_URL`.
   - `alembic revision --autogenerate -m "schema inicial"` con todos los modelos
     importados.
   - Quitar `Base.metadata.create_all(bind=engine)` de `app/main.py` (dejarlo solo
     en `tests/conftest.py`).
   - Deploy y CI corren `alembic upgrade head` antes de arrancar.
4. **`seed.py`** contra la nueva base (o convertirlo en una migración de datos).
5. **Higiene:** `.env.example` con `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`;
   confirmar que `miifts.db` no se vuelva a trackear (ya está en `.gitignore`).
6. **Deploy del backend:** Render / Railway / Fly.io (free). Dockerfile o buildpack
   de Python; setear las env vars; `GET /health` como health check.

Todo esto está desglosado en `SPRINT_2.md` (Integrantes 2 y 3).
