# miIFTS — Backend MVP

## Qué es

API REST para que un estudiante del IFTS lleve el seguimiento de su carrera:
consultar el plan de estudios, registrar sus cursadas y notas, guardar material
de estudio y anotar fechas de parciales/finales. Incluye un rol **admin** que
administra el catálogo académico.

## Stack

FastAPI + SQLAlchemy + PostgreSQL (gestionado en la nube). Auth con JWT
(HS256, 24 h). Passwords con bcrypt. Arquitectura por capas y por feature:
`router → service → repository → model`, con `app/shared/` para paginación y
jerarquía de errores. Swagger en `/docs`.

### Persistencia

La capa de persistencia está pensada para vivir en la nube desde el MVP, no como
un agregado posterior:

- **Motor de base de datos**: PostgreSQL gestionado (por ejemplo Supabase, Neon,
  Railway o RDS) como entorno de staging/producción. SQLite queda solo como motor
  local para desarrollo rápido y para correr los tests, nunca como destino de
  despliegue — evita el problema de filesystem efímero de la mayoría de los
  hosting cloud (los contenedores no garantizan disco persistente entre deploys)
  y el hecho de que SQLite no soporta bien escrituras concurrentes desde
  múltiples instancias.
- **Configuración por variable de entorno**: la connection string vive en
  `DATABASE_URL` (con fallback a un SQLite local si no está seteada, para no
  romper el entorno de desarrollo). Nada de credenciales hardcodeadas; se maneja
  con `.env` + `pydantic-settings` en local y variables de entorno del proveedor
  en la nube.
- **Pooling de conexiones**: `SQLAlchemy` con `pool_pre_ping=True` y un pool
  acotado (`pool_size` / `max_overflow`) para no agotar las conexiones que suelen
  limitar los planes gratuitos/chicos de Postgres gestionado.
- **Migraciones versionadas**: se incorpora **Alembic** desde el arranque del
  proyecto en lugar de `Base.metadata.create_all()`. Esto es necesario apenas hay
  una base remota compartida entre entornos (dev/staging/prod) — sin migraciones
  versionadas, cualquier cambio de modelo rompe la base en la nube.
- **Backups**: se delega en el backup automático del proveedor gestionado
  (point-in-time recovery cuando el plan lo incluye) en vez de implementar backup
  propio para el MVP.
- **TLS**: la conexión a la base en la nube se fuerza con `sslmode=require` (o el
  equivalente del driver) ya que el tráfico sale a internet.

## Funcionalidades

### Autenticación y roles

Registro (siempre rol estudiante; el rol del body se ignora → sin escalada de
privilegios), login (JSON para el front, form OAuth2 para Swagger), `/auth/me`,
`/auth/verify`.

Dos roles: estudiante y admin. Dependencias `get_current_user` (401) y
`require_admin` (403).

### Catálogo académico (`/materias`)

Estructura: IFTS → Carrera → Materia → Correlativas.

Lectura pública: listar carreras, materias por carrera (paginado), búsqueda por
nombre/código con filtros de año y cuatrimestre, correlativas.

Escritura (carreras y materias): solo admin. Con validaciones (año 1–6,
cuatrimestre 1/2, duración 1–12) y reglas de negocio (no borrar carrera con
materias, no borrar materia con cursadas, código de materia único por
carrera → 409).

### Cursadas y promedio (`/materias/usuario`, `/materias/cursada`, `/materias/promedio`)

El alumno registra las materias que cursa/aprobó, con notas parciales y final
(1–10).

Identidad tomada del token JWT; un alumno solo ve/gestiona lo suyo (403 si es de
otro), un admin puede consultar cualquiera.

Regla: solo se puede cargar una materia de la carrera del alumno. Cálculo de
promedio sobre notas finales.

### Recursos de estudio (`/recursos`, `/convenios`, `/talentotech`)

Recursos: links de material por materia, con dueño. Lectura pública con filtros
(materia, tipo, rango de fechas) y paginación. Crear requiere login;
editar/borrar solo el dueño (403 si no).

Convenios y cursos TalentoTech: lectura pública; alta/edición/baja solo admin.

### Recordatorios (`/recordatorios`)

Agenda de fechas (parcial/tp/final/otro) del alumno. Identidad del token. Listado
paginado con filtros por tipo, materia y rango de fechas. Validación de fecha
futura (422).

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

## Estado actual — qué falta para cerrar este MVP

Lo que ya está implementado y probado (60 tests, coverage ~81%): auth + roles,
catálogo con validaciones y reglas de negocio, cursadas/promedio, recursos con
ownership, recordatorios con fecha futura, paginación en todos los listados,
jerarquía de errores unificada. **Falta** para que el MVP sea el descrito arriba:

| # | Brecha | Detalle | Sprint 2 |
|---|--------|---------|----------|
| 1 | **Identidad desde el token incompleta** | El MVP dice "identidad tomada del token; un alumno solo ve/gestiona lo suyo (403)". Hoy eso rige para **recursos**, pero **cursadas y recordatorios** reciben `usuario_id` por path/query sin validarlo contra el JWT, y `get_usuario_actual()` en `materias/router.py` está **hardcodeado a `1`**. | Integrante 1 |
| 2 | **Persistencia sigue en SQLite local** | `app/database.py` ya lee `DATABASE_URL`, pero no hay Postgres gestionado, ni Alembic (el schema se crea con `create_all()`), ni `pydantic-settings`, ni pool tuneado, ni `sslmode`. | Integrante 2 |
| 3 | **Sin deploy y sin CI que bloquee** | No hay Dockerfile ni hosting. `pydantic` **no está pinneado** en `requirements.txt` y el CI está seteado a Python 3.12 pero **nunca se confirmó que corra ni que gatee PRs** (por eso pasó a `dev` un bug que sólo se ve en Python < 3.14). Falta branch protection en `dev`/`main`. | Integrante 3 |
| 4 | **Contrato incompleto para el front** | Faltan `GET /materias/{id}` y `GET /materias/carreras/{id}` (detalle). CORS default sólo `localhost:5173`. `api-requests.http` desactualizado. Sin documento de integración. | Integrante 4 |
| 5 | **Deuda de calidad** | `class Config` de Pydantic v2 deprecado, `black` sin correr ni gate, `datetime.utcnow()` deprecado, `python-jose` (2021) sin mantenimiento, imports muertos, schemas `*Filter` sin uso, coverage bajo en repos de recursos. | Integrante 5 |

Desglose completo con tareas y cronograma en **`SPRINT_2.md`**.

---

## Fuera de alcance del MVP (no van al Sprint 2)

- Recuperación de contraseña, refresh token, logout real (JWT stateless).
- Carga de archivos: los recursos son solo links.
- Notificaciones de recordatorios (mails / push).
- Multi-IFTS en el front (el modelo lo soporta; el seed carga uno).
- Panel de administración de usuarios (el admin se crea por seed o a mano).
- Rate limiting, auditoría, métricas de negocio.

---

## Integración con el front (dentro del MVP)

1. **Fuente de verdad = OpenAPI** (`GET /openapi.json`, Swagger en `/docs`).
   Generar cliente tipado con `openapi-typescript` u `orval`.
2. **Auth**: `POST /auth/login` → `{ access_token, usuario }`. Guardar el token,
   mandarlo en `Authorization: Bearer`. `401` → a login; `403` → sin permiso.
3. **Respuestas** (contrato unificado): listas → `res.items` + `res.total_pages`;
   errores → `res.detail` (string), y `res.errors` (`[{campo, msg}]`) para marcar
   campos en formularios.
4. **Pantallas MVP**: registro/login · plan de estudios (carreras → materias →
   correlativas) · mis cursadas + promedio · recursos (lista con filtros + alta) ·
   recordatorios (agenda).
5. **Requisitos que el backend debe entregar** (Sprint 2, Integrantes 1 y 4):
   endpoints de detalle, CORS con el origin del front, y la identidad real desde
   el token para "mis cursadas / mis recordatorios".
