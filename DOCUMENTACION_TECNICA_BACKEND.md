# Documentación Técnica - Backend miIFTS

## Resumen General

**miIFTS API** es una API RESTful construida con **FastAPI** para un Instituto de Formación Técnica Superior. Gestiona usuarios, materias, cursadas, recursos académicos, recordatorios, convenios interinstitucionales, cursos TalentoTech y notificaciones push.

---

## Stack Tecnológico

| Capa | Tecnología | Versión | Propósito |
|------|------------|---------|-----------|
| **Framework Web** | FastAPI | 0.115.5 | API REST, validación automática, OpenAPI nativo |
| **Servidor ASGI** | Uvicorn | 0.32.1 | Ejecución de la app FastAPI |
| **ORM** | SQLAlchemy | 2.0.36 | Mapeo objeto-relacional, queries type-safe |
| **Migraciones** | Alembic | 1.14.0 | Versionado de esquema de BD |
| **Base de Datos** | SQLite / PostgreSQL | — | Persistencia (SQLite default, PostgreSQL vía `DATABASE_URL`) |
| **Validación** | Pydantic v2 | 2.13.4 | Schemas de entrada/salida, serialización ORM |
| **Auth JWT** | python-jose | 3.3.0 | Tokens HS256 stateless |
| **Hashing** | passlib + bcrypt | 1.7.4 / 4.0.1 | Contraseñas seguras |
| **Notificaciones Push** | pywebpush | ≥1.13 | Web Push Protocol (VAPID) |
| **Scheduler** | APScheduler | ≥3.10 | Jobs periódicos (recordatorios push) |
| **Email** | smtplib (stdlib) | — | Envío de emails de reset password |
| **Testing** | pytest + pytest-cov | 8.3.3 / 5.0.0 | Tests unitarios/integración con SQLite en memoria |
| **Calidad** | black + pylint | 24.8.0 / 3.2.7 | Formateo y linting |

---

## Arquitectura

**Patrón por Feature (4 capas + router):**

```
Router → Service → Repository → Database (SQLAlchemy)
```

Cada feature en `app/features/{dominio}/` contiene:
- `model.py` — Modelos SQLAlchemy (tablas, relaciones, constraints)
- `schema.py` — Schemas Pydantic (request/response, validación)
- `repository.py` — Acceso a datos (CRUD, queries específicas)
- `service.py` — Lógica de negocio (orquesta repository, reglas, excepciones)
- `router.py` — Endpoints FastAPI (dependencias, status codes, response_model)

**Excepciones:** Jerarquía única en `app/shared/exceptions.py` (heredan de `HTTPException`). Los services lanzan excepciones de dominio; los routers no necesitan try/except.

**Paginación:** Dependencia reutilizable `PaginationParams` (`page`, `per_page`) + helper `paginate()` → `PaginatedResponse`.

---

## Mapa de Funcionalidades por Dominio

---

### 1. Autenticación (`/auth`)

| Endpoint | Método | Descripción | Auth | Tecnologías Clave |
|----------|--------|-------------|------|-------------------|
| `/registro` | POST | Registra usuario (email único, nombre, apellido, password, carrera_id, rol) | ❌ | bcrypt, JWT, SQLAlchemy |
| `/login` | POST | Autentica y devuelve JWT (24h, HS256, payload: `sub`=user_id, `email`) | ❌ | python-jose, bcrypt |
| `/me` | GET | Perfil del usuario autenticado | ✅ JWT | OAuth2PasswordBearer |
| `/me` | PATCH | Actualiza nombre/apellido del usuario autenticado | ✅ JWT | — |
| `/verify` | GET | Valida token JWT (devuelve `valid=true`, `user_id`) | ✅ JWT | — |
| `/forgot-password` | POST | Solicita reset de contraseña (siempre mismo mensaje por seguridad) | ❌ | secrets, hashlib (SHA256), email (SMTP) |
| `/reset-password` | POST | Consume token de un uso y actualiza contraseña | ❌ | SHA256 token hash, bcrypt |
| `/password` | PATCH | Cambia contraseña (requiere contraseña actual como re-autenticación) | ✅ JWT | bcrypt |

**Modelos:** `Usuario` (id, nombre, apellido, email único, password_hash, carrera_id FK, rol enum: estudiante/admin, fecha_registro), `PasswordResetToken` (token_hash SHA256, expira 30 min, usado bool).

**Seguridad:** Password nunca expuesto en respuestas (`password_hash` excluido en schemas). Token JWT en header `Authorization: Bearer <token>`.

---

### 2. Materias y Cursadas (`/materias`)

#### 2.1 Carreras e IFTS
| Endpoint | Método | Descripción | Auth | Reglas |
|----------|--------|-------------|------|--------|
| `/carreras` | GET | Lista paginada de carreras | ❌ | Lectura pública |
| `/carreras` | POST | Crea carrera (nombre, duración, ifts_id) | ✅ Admin | — |
| `/carreras/{id}` | PUT | Actualiza carrera | ✅ Admin | — |
| `/carreras/{id}` | DELETE | Elimina carrera | ✅ Admin | Bloquea si tiene materias asociadas |
| `/carreras/{id}` | GET | Detalle de carrera | ❌ | — |

#### 2.2 Materias
| Endpoint | Método | Descripción | Auth | Reglas |
|----------|--------|-------------|------|--------|
| `/carrera/{carrera_id}` | GET | Materias por carrera (paginado) | ❌ | Código único por carrera (UniqueConstraint) |
| `/buscar` | GET | Búsqueda texto libre (`q`) + filtros opcionales `anio`, `cuatrimestre` | ❌ | Nuevo endpoint dedicado (RF-21) |
| `/{materia_id}` | GET | Detalle de materia | ❌ | — |
| `/` | POST | Crea materia (nombre, código, año, cuatrimestre, carrera_id) | ✅ Admin | Código único por carrera |
| `/{materia_id}` | PUT | Actualiza materia | ✅ Admin | — |
| `/{materia_id}` | DELETE | Elimina materia | ✅ Admin | Bloquea si tiene cursadas asociadas |

#### 2.3 Correlativas
| Endpoint | Método | Descripción | Auth | Reglas |
|----------|--------|-------------|------|--------|
| `/correlativas/{materia_id}` | GET | Correlativas de una materia (paginado) | ❌ | — |
| `/correlativas` | POST | Crea correlativa (`materia_id` → `requiere_id`) | ✅ Admin | Valida existencia de ambas materias + **detección de ciclos** (DFS en grafo) |
| `/correlativas/{id}` | DELETE | Elimina correlativa | ✅ Admin | — |

#### 2.4 Cursadas (MateriaUsuario)
| Endpoint | Método | Descripción | Auth | Reglas |
|----------|--------|-------------|------|--------|
| `/usuario/{usuario_id}` | GET | Cursadas del usuario (paginado) | ✅ Propio o Admin | Usuario solo ve las suyas |
| `/promedio/{usuario_id}` | GET | Promedio de notas finales (excluye `cursando` y `pendiente`) | ✅ Propio o Admin | Cálculo: promocionada = promedio parciales; aprobada/desaprobada = examen_final |
| `/usuario` | POST | Agrega cursada (materia_id, cursando, notas opcionales) | ✅ Usuario logueado | Valida que materia pertenezca a carrera del usuario; única por usuario+materia |
| `/cursada/{id}` | PATCH | Actualiza cursada (notas, cursando, examen_final) | ✅ Usuario logueado | Solo dueño |
| `/cursada/{id}` | DELETE | Elimina cursada | ✅ Usuario logueado | Solo dueño |

**Lógica de negocio (service):**
- `promociona_por_parciales`: ambos parciales ≥ 7 → promocionada (exime final)
- `derivar_estado_cursada`: cursando → "cursando"; promocionada → "promocionada"; con examen_final ≥ 4 → "aprobada", < 4 → "desaprobada"; sin examen → "pendiente"
- `derivar_nota_final`: si promocionó → promedio parciales; si no → examen_final

**Modelos:** `IFTS`, `Carrera`, `Materia` (unique carrera+codigo), `Correlativa` (unique materia+requiere, recursiva), `MateriaUsuario` (unique usuario+materia, notas, cursando bool, estado/nota_final calculados en service).

---

### 3. Recursos Académicos (`/recursos`)

| Endpoint | Método | Descripción | Auth | Filtros/Orden |
|----------|--------|-------------|------|---------------|
| `/` | GET | Lista global con filtros | ❌ | `materia_id`, `tipo`, `desde` (date), `hasta` (date), paginado |
| `/{id}` | GET | Detalle de recurso | ❌ | — |
| `/` | POST | Crea recurso (titulo, url, descripcion, tipo, materia_id) | ✅ Usuario | Asocia a `usuario_id` del token |
| `/{id}` | PUT | Actualiza recurso | ✅ Propietario | Solo dueño puede modificar |
| `/{id}` | DELETE | Elimina recurso | ✅ Propietario | Solo dueño puede eliminar |
| `/usuario/{usuario_id}` | GET | Recursos por usuario (paginado) | ❌ | — |
| `/materia/{materia_id}` | GET | Recursos por materia (paginado) | ❌ | — |

**Modelo:** `Recurso` (id, usuario_id FK, materia_id FK, titulo, url, descripcion, **tipo** nullable, fecha_creacion). Campo `tipo` agregado para filtro RF-16 (pdf, video, etc.).

---

### 4. Convenios Interinstitucionales (`/convenios`)

| Endpoint | Método | Descripción | Auth |
|----------|--------|-------------|------|
| `/` | GET | Lista todos (paginado) | ❌ |
| `/{id}` | GET | Detalle | ❌ |
| `/carrera/{carrera_id}` | GET | Por carrera (paginado) | ❌ |
| `/` | POST | Crea (institucion, carrera_destino, descripcion, link_info, carrera_id) | ✅ Admin |
| `/{id}` | PUT | Actualiza | ✅ Admin |
| `/{id}` | DELETE | Elimina | ✅ Admin |

**Modelo:** `Convenio` (id, carrera_id FK, institucion, carrera_destino, descripcion, link_info).

---

### 5. TalentoTech (`/talentotech`)

| Endpoint | Método | Descripción | Auth |
|----------|--------|-------------|------|
| `/` | GET | Lista todos (paginado) | ❌ |
| `/{id}` | GET | Detalle | ❌ |
| `/carrera/{carrera_id}` | GET | Por carrera (paginado) | ❌ |
| `/categoria/{categoria}` | GET | Por categoría (paginado) | ❌ |
| `/` | POST | Crea (nombre_curso, categoria, descripcion, duracion, link_inscripcion, carrera_id) | ✅ Admin |
| `/{id}` | PUT | Actualiza | ✅ Admin |
| `/{id}` | DELETE | Elimina | ✅ Admin |

**Modelo:** `TalentoTech` (id, carrera_id FK, nombre_curso, categoria, descripcion, duracion, link_inscripcion).

---

### 6. Recordatorios (`/recordatorios`)

| Endpoint | Método | Descripción | Auth | Filtros |
|----------|--------|-------------|------|---------|
| `/` | GET | Lista del usuario autenticado (paginado, orden fecha descendente) | ✅ Usuario | `tipo`, `desde` (date), `hasta` (date), `materia_id` |
| `/` | POST | Crea (titulo, fecha, tipo, materia_id opcional) | ✅ Usuario | Asocia a `usuario_id` del token |
| `/{id}` | PATCH | Actualiza (campos parciales) | ✅ Usuario | Solo dueño |
| `/{id}` | DELETE | Elimina | ✅ Usuario | Solo dueño |

**Tipos de recordatorio:** "parcial", "tp", "final", "otro" (string libre validado en frontend).

**Modelo:** `Recordatorio` (id, titulo, fecha DateTime, tipo, usuario_id FK, materia_id FK nullable).

---

### 7. Notificaciones Push (`/notificaciones`)

| Endpoint | Método | Descripción | Auth |
|----------|--------|-------------|------|
| `/suscripcion` | POST | Registra/actualiza suscripción push (endpoint, p256dh, auth) | ✅ Usuario |
| `/suscripcion` | DELETE | Elimina suscripción por endpoint | ✅ Usuario |

**Flujo Push:**
1. Frontend (PWA) solicita permisos → obtiene `PushSubscription` del navegador (endpoint, keys p256dh/auth)
2. Frontend llama `POST /notificaciones/suscripcion` con esos datos
3. Backend guarda en `PushSubscription` (unique constraint usuario+endpoint)
4. **Scheduler (APScheduler)** cada 5 min (configurable `PUSH_SCHEDULER_INTERVAL_MINUTES`):
   - Busca recordatorios próximos a vencer
   - Envía push vía `pywebpush` con claves VAPID
   - Limpia automáticamente suscripciones que responden 404/410 (gone)
5. Claves VAPID en variables de entorno: `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_CLAIMS_SUB`

**Modelo:** `PushSubscription` (id, usuario_id FK, endpoint unique, p256dh, auth, fecha_creación, unique constraint compuesto usuario+endpoint).

**Notas:** HTTPS obligatorio (localhost válido en dev). iOS 16.4+ requiere PWA instalada ("Añadir a pantalla de inicio"). Android funciona con PWA cerrada.

---

## Configuración y Variables de Entorno (`.env`)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./miifts.db` | Conexión BD (PostgreSQL en prod) |
| `SECRET_KEY` | fallback inseguro | Firma JWT HS256 (**cambiar en prod**) |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Orígenes permitidos CORS |
| `FRONTEND_RESET_PASSWORD_URL` | `http://localhost:5173/reset-password` | Link en email de reset |
| `VAPID_PUBLIC_KEY` | — | Clave pública VAPID (push) |
| `VAPID_PRIVATE_KEY` | — | Clave privada VAPID (push) |
| `VAPID_CLAIMS_SUB` | `mailto:admin@miifts.com` | Subject VAPID |
| `PUSH_SCHEDULER_INTERVAL_MINUTES` | `5` | Intervalo job recordatorios push |

---

## Base de Datos - Esquema Principal

| Tabla | PK | FKs Clave | Índices / Constraints |
|-------|----|-----------|------------------------|
| `usuarios` | id | carrera_id → carreras | email unique, idx |
| `carreras` | id | ifts_id → ifts | — |
| `ifts` | id | — | — |
| `materias` | id | carrera_id → carreras | unique(carrera_id, codigo) |
| `correlativas` | id | materia_id, requiere_id → materias | unique(materia_id, requiere_id) |
| `materias_usuario` | id | usuario_id → usuarios, materia_id → materias | unique(usuario_id, materia_id) |
| `recordatorios` | id | usuario_id → usuarios, materia_id → materias | idx usuario_id, materia_id |
| `recursos` | id | usuario_id → usuarios, materia_id → materias | idx usuario_id, materia_id |
| `convenios` | id | carrera_id → carreras | idx carrera_id |
| `talentotech` | id | carrera_id → carreras | idx carrera_id |
| `push_subscriptions` | id | usuario_id → usuarios | endpoint unique, unique(usuario_id, endpoint) |

---

## Testing

- **Framework:** pytest + pytest-cov
- **BD de test:** SQLite en memoria (`sqlite:///:memory:`) con `StaticPool`
- **Cliente:** `TestClient` de FastAPI con `dependency_overrides` para `get_db`
- **Fixtures (`conftest.py`):** `client`, `db_session`, `carrera_test`, `usuario_payload`, `usuario_registrado`, `auth_headers`
- **Tests existentes:** `test_auth.py`, `test_materias.py`, `test_recursos.py`, `test_recordatorios.py`, `test_correlativas.py`, `test_authorization.py`, `test_estructura_respuestas.py`, `test_validaciones.py`

---

## Convenciones y Decisiones Clave

1. **Pydantic v2:** `from_attributes = True` en todos los response schemas para mapeo directo ORM → schema.
2. **Naming:** Tablas snake_case explícitas (`__tablename__`).
3. **Excepciones de dominio:** Services lanzan `NotFoundError`, `DuplicateError`, `BusinessRuleError`, `UnauthorizedError`, `BadRequestError`, `ForbiddenError`; routers propagan automáticamente.
4. **Auth en dependencias:** `get_current_user` (JWT), `require_admin` (rol admin), `solo_propio_o_admin` (usuario dueño o admin).
5. **Seed:** `seed.py` hace `drop_all` + `create_all` + carga IFTS, carreras, materias iniciales.
6. **Documentación OpenAPI:** Generada automáticamente por FastAPI (`/docs`, `/redoc`, `docs/openapi.json` via script).

---

## Endpoints Resumen (OpenAPI Tags)

- **auth** — Registro, login, perfil, reset password, verify token
- **materias** — Carreras, materias, correlativas, cursadas, promedio, búsqueda
- **recursos** — Recursos académicos (CRUD + filtros), convenios, talentotech
- **recordatorios** — CRUD recordatorios con filtros y paginación
- **notificaciones** — Suscripciones push, envío programado (interno)

---

## Limitaciones Conocidas / Pendientes

- `get_usuario_actual()` en materias/router.py usa hardcode `1` — pendiente migración completa a JWT real.
- Algunos endpoints de recursos/convenios/talentotech no tienen auth implementado en todos los métodos (según sprint actual).
- Búsqueda de materias (`/materias/buscar`) implementada pero requiere validación de integración frontend.
- Notificaciones push requieren configuración VAPID en producción y HTTPS.