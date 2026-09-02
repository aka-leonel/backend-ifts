# Sprint 2 de 4 días - Backend miIFTS
**Objetivo:** Cerrar el MVP real — identidad desde el token en toda la API,
PostgreSQL gestionado con migraciones, deploy con CI que bloquee, contrato
estable para el front y saldo de deuda técnica.

> Contexto: ver `MVP.md` (definición del MVP + brechas) y `README.md`
> (contrato de respuestas, jerarquía de errores). Estado de partida:
> 60 tests, coverage ~81%, todo sobre SQLite local.

---

## 📊 Distribución de Tareas por Integrante

### 🔐 **Integrante 1 - IDENTIDAD DESDE EL TOKEN**
**Prioridad:** ALTA | **Complejidad:** Media | **Días:** 3

Hoy `cursadas` y `recordatorios` reciben `usuario_id` por path/query sin
validarlo contra el JWT, y `get_usuario_actual()` en `materias/router.py`
devuelve `1` hardcodeado. El MVP dice "un alumno solo ve/gestiona lo suyo (403)".

#### Tareas:
1. **Cursadas por token**
   - `POST /materias/usuario/{usuario_id}`, `PATCH /materias/cursada/{id}`,
     `DELETE /materias/cursada/{id}`: reemplazar el `usuario_id` de path y el
     `get_usuario_actual()` hardcodeado por `Depends(get_current_user)`.
   - `GET /materias/usuario/{usuario_id}` y `GET /materias/promedio/{usuario_id}`:
     permitir sólo si `usuario_id == current_user.id` **o** `current_user.rol == admin`;
     si no, `403` (usar `ForbiddenError` de `app/shared/exceptions.py`).
   - Borrar la función `get_usuario_actual()`.

2. **Recordatorios por token**
   - `POST /recordatorios/`, `GET /recordatorios/`, `DELETE /recordatorios/{id}`:
     sacar el query param `usuario_id`, tomar la identidad de `get_current_user`.
   - Un alumno sólo ve/borra los suyos; `404` si el recordatorio es de otro
     (no revelar existencia).

3. **Helper reutilizable**
   ```python
   # app/features/auth/dependencies.py
   def solo_propio_o_admin(usuario_id: int, actual: UsuarioResponse = Depends(get_current_user)):
       if actual.id != usuario_id and actual.rol != RolUsuario.ADMIN:
           raise ForbiddenError("Sólo podés acceder a tus propios datos")
       return actual
   ```

**Entregables:**
- [ ] Ningún endpoint de cursadas/recordatorios acepta `usuario_id` sin verificar el token
- [ ] `get_usuario_actual()` eliminado
- [ ] Tests: alumno accede a lo suyo (200), a lo de otro (403/404), admin a cualquiera (200) — mínimo 6
- [ ] `api-requests.http` y Swagger reflejan que ya no se manda `usuario_id`

---

### 🗄️ **Integrante 2 - POSTGRESQL GESTIONADO + MIGRACIONES**
**Prioridad:** ALTA | **Complejidad:** Media-Alta | **Días:** 4

#### Tareas:
1. **Config con `pydantic-settings`**
   ```python
   # app/config.py
   class Settings(BaseSettings):
       database_url: str = "sqlite:///./miifts.db"
       secret_key: str
       cors_origins: str = "http://localhost:5173"
       model_config = SettingsConfigDict(env_file=".env")
   ```
   - Reemplazar los `os.getenv` sueltos de `database.py`, `auth/service.py` y
     `main.py`. Quitar el default hardcodeado de `SECRET_KEY`.
   - Crear `.env.example` con todas las variables documentadas.

2. **Engine listo para la nube**
   ```python
   engine = create_engine(
       settings.database_url,
       pool_pre_ping=True,
       pool_size=5, max_overflow=5,
       connect_args={"sslmode": "require"} if "postgresql" in settings.database_url else
                    {"check_same_thread": False},
   )
   ```
   - Agregar `psycopg[binary]` a `requirements.txt`. SQLite sigue funcionando en local/tests.

3. **Alembic**
   - `alembic init alembic`; `env.py` que lea `settings.database_url` e importe
     todos los modelos (`app.features.*.model`) para el autogenerate.
   - `alembic revision --autogenerate -m "schema inicial"` — revisar el script a mano.
   - **Quitar** `Base.metadata.create_all(bind=engine)` de `app/main.py`
     (dejarlo sólo en `tests/conftest.py`).
   - Documentar el flujo en README: `alembic upgrade head`, cómo generar una nueva.

4. **Base en la nube**
   - Crear un Postgres gestionado (Neon / Supabase / Railway, free tier).
   - Correr `alembic upgrade head` + `python seed.py` contra esa base.
   - Confirmar backups automáticos activos en el proveedor.

**Entregables:**
- [ ] `DATABASE_URL` de Postgres funcionando en un entorno remoto
- [ ] `alembic upgrade head` levanta el schema desde cero; `create_all()` fuera de `main.py`
- [ ] `.env.example` completo + sección de migraciones y DB en README
- [ ] Tests siguen verdes en SQLite (sin tocar la lógica de negocio)

---

### 🚀 **Integrante 3 - DEPLOY + CI QUE BLOQUEE**
**Prioridad:** ALTA | **Complejidad:** Media | **Días:** 3-4

En Sprint 1 pasó a `dev` un bug que sólo se ve en Python < 3.14 porque el CI
nunca se confirmó corriendo ni bloqueando PRs, y `pydantic` no está pinneado.

#### Tareas:
1. **Reproducibilidad**
   - Pinnear **todas** las libs sin versión en `requirements.txt` (empezando por
     `pydantic`, `pydantic-settings`, `psycopg`).
   - Fijar **una** versión de Python: `.python-version` + `python-version` del
     workflow + `README`. (Sugerencia: 3.12, la del CI actual.)
   - `datetime.utcnow()` → `datetime.now(timezone.utc)` en `auth/service.py`.

2. **CI real**
   - Verificar que `.github/workflows/tests.yml` corre en cada PR a `dev`/`main`
     y que **falla** si fallan los tests o el coverage < 60%.
   - Activar **branch protection** en `dev` y `main`: requerir el check "Tests"
     y ≥1 review antes de mergear.
   - Agregar al workflow un job que levante la app con Postgres
     (`services: postgres:` de GitHub Actions) y corra `alembic upgrade head`.

3. **Deploy del backend**
   - `Dockerfile` (python slim, `pip install -r requirements.txt`,
     `alembic upgrade head && uvicorn app.main:app`).
   - Deploy en Render / Railway / Fly.io (free). Variables: `DATABASE_URL`,
     `SECRET_KEY`, `CORS_ORIGINS`. Health check en `GET /health`.
   - Documentar el proceso en `README` (o `DEPLOY.md`).

**Entregables:**
- [ ] `requirements.txt` 100% pinneado y versión de Python única y documentada
- [ ] CI corre en PRs y **bloquea** merge si algo falla (branch protection activo)
- [ ] Backend desplegado y accesible por URL pública, con `/docs` y `/health` OK
- [ ] `Dockerfile` + doc de deploy

---

### 🔌 **Integrante 4 - CONTRATO PARA EL FRONT**
**Prioridad:** MEDIA | **Complejidad:** Baja-Media | **Días:** 3

#### Tareas:
1. **Endpoints de detalle que faltan**
   - `GET /materias/{materia_id}` → `MateriaResponse` (404 si no existe).
   - `GET /materias/carreras/{carrera_id}` → `CarreraResponse` (404 si no existe).
   - Lectura pública, con su test.

2. **CORS y OpenAPI**
   - `CORS_ORIGINS` con el/los origin(es) reales del front (dev y deploy).
   - Exportar el `openapi.json` a `docs/openapi.json` (script en `Makefile` o
     `scripts/`) para que el front genere el cliente sin levantar el backend.
   - Ejemplos (`examples=`) en los schemas de request más usados para que
     Swagger muestre payloads copiables.

3. **Documentación de integración**
   - `docs/INTEGRACION_FRONT.md`: flujo de auth paso a paso, tabla de shapes de
     respuesta (colección / recurso / 204 / error), cómo paginar, cómo mapear
     `errors[]` a campos de formulario, lista de endpoints por pantalla del MVP.
   - Actualizar `api-requests.http` con todos los endpoints al día (auth, sin
     `usuario_id` en query, paginación).

**Entregables:**
- [ ] `GET /materias/{id}` y `GET /materias/carreras/{id}` con tests
- [ ] `docs/openapi.json` versionado + `docs/INTEGRACION_FRONT.md`
- [ ] `api-requests.http` actualizado y CORS configurado para el front

---

### 🧹 **Integrante 5 - CALIDAD Y DEUDA TÉCNICA**
**Prioridad:** MEDIA | **Complejidad:** Baja-Media | **Días:** 3

#### Tareas:
1. **Pydantic v2 al día**
   - Migrar `class Config: from_attributes = True` → `model_config = ConfigDict(from_attributes=True)`
     en todos los schemas (elimina ~15 `PydanticDeprecatedSince20`).
   - Borrar imports muertos: `get_current_user` en `recursos/schema.py`.
   - Evaluar y, si no se usan, eliminar los schemas `MateriaSearchQuery`,
     `RecordatorioFilter`, `RecursoFilter`.

2. **Formato y lint como gate**
   - Correr `black app tests` sobre todo el repo (un commit "style: black").
   - Cambiar el workflow: `black --check` y `pylint` pasan de informativos a
     **bloqueantes** (quitar el `|| true` / `--exit-zero`), con un
     `.pylintrc` que desactive lo que no aplica al proyecto.

3. **Auth y cobertura**
   - Evaluar reemplazar `python-jose` (2021, sin mantenimiento) por `pyjwt`;
     si el cambio es acotado, hacerlo; si no, dejar una nota en README.
   - Subir coverage de `recursos/repository.py` y `recursos/service.py`
     (hoy 28–50%) con tests de repository directos.

**Entregables:**
- [ ] Cero warnings de deprecación de Pydantic al correr los tests
- [ ] `black` y `pylint` bloqueantes en CI; repo formateado
- [ ] Coverage total ≥ 80% y ningún módulo de `app/` por debajo de 50%
- [ ] Decisión documentada sobre `python-jose` vs `pyjwt`

---

## 📅 Cronograma sugerido

### **Día 1**
- Todos: pull de `dev`, `git checkout -b feature/tu-nombre-tarea`.
- Int. 1: cursadas por token.
- Int. 2: `pydantic-settings` + `.env.example` + engine para Postgres.
- Int. 3: pinnear `requirements.txt` + fijar versión de Python.
- Int. 4: `GET /materias/{id}` y `GET /materias/carreras/{id}`.
- Int. 5: migración `class Config` → `ConfigDict`.

### **Día 2**
- Int. 1: recordatorios por token + helper `solo_propio_o_admin`.
- Int. 2: `alembic init` + migración inicial + quitar `create_all()` de `main.py`.
- Int. 3: verificar CI corriendo + branch protection en `dev`/`main`.
- Int. 4: CORS + export de `openapi.json` + ejemplos en Swagger.
- Int. 5: `black` en todo el repo + `.pylintrc`.

### **Día 3**
- Int. 1: tests de identidad (alumno propio / ajeno / admin).
- Int. 2: base Postgres en la nube + `alembic upgrade head` + `seed.py`.
- Int. 3: `Dockerfile` + deploy del backend + `/health`.
- Int. 4: `docs/INTEGRACION_FRONT.md` + `api-requests.http`.
- Int. 5: coverage de repos de recursos + decisión `python-jose`/`pyjwt`.

### **Día 4**
- Todos: testing cruzado contra el backend desplegado.
- Int. 3: job de CI con Postgres + `alembic upgrade head`.
- Todos: actualizar `README` / `MVP.md` con lo cerrado.
- Todos: PR a `dev`, code review en pares, merge sin conflictos.

---

## ✅ Criterios de aceptación

1. **Seguridad / identidad:**
   - [ ] Ningún endpoint acepta `usuario_id` por path/query sin validar el token.
   - [ ] Alumno accede sólo a lo suyo (403/404 si no); admin a todo.

2. **Persistencia:**
   - [ ] Backend corre contra PostgreSQL gestionado con `DATABASE_URL`.
   - [ ] Schema versionado con Alembic; `create_all()` sólo en tests.
   - [ ] `SECRET_KEY` sin default hardcodeado.

3. **Deploy / CI:**
   - [ ] Backend accesible por URL pública (`/docs`, `/health`).
   - [ ] CI corre en cada PR y **bloquea** el merge si falla; branch protection activo.
   - [ ] `requirements.txt` pinneado y una sola versión de Python.

4. **Front-ready:**
   - [ ] Endpoints de detalle disponibles + `openapi.json` versionado.
   - [ ] `docs/INTEGRACION_FRONT.md` y `api-requests.http` al día.

5. **Calidad:**
   - [ ] Sin warnings de deprecación de Pydantic.
   - [ ] `black`/`pylint` bloqueantes; coverage ≥ 80%.

6. **Proceso:**
   - [ ] Cada feature en su rama; PRs revisados por ≥1 compañero; sin conflictos.

---

## 🚀 Bonus (si sobra tiempo)

1. **Docker Compose** para dev (app + Postgres local, un solo `docker compose up`).
2. **Logging estructurado** con `loguru` en las operaciones críticas.
3. **Refresh token** + endpoint de logout con lista de revocación.
4. **Recuperación de contraseña** por email (token de un solo uso).
5. **Rate limiting** básico en `/auth/login` y `/auth/registro`.
6. **Seed idempotente** (que no falle si ya hay datos).

---

## 📞 Coordinación

### Daily Standup (10 min)
- ¿Qué hice ayer? ¿Qué haré hoy? ¿Tengo algún blocker?

### Git Flow
```bash
git checkout dev
git pull origin dev
git checkout -b feature/tu-nombre-tarea

git add .
git commit -m "feat: descripción clara"
git push origin feature/tu-nombre-tarea
# PR en GitHub: feature/tu-nombre → dev (requiere CI verde + 1 review)
```

---

## 🎯 Métricas de éxito

Al final del sprint:
- Endpoints con identidad validada por token: objetivo 100%.
- Entorno de despliegue sobre PostgreSQL gestionado: objetivo funcionando.
- PRs que pasan por CI bloqueante: objetivo 100%.
- Cobertura de tests: objetivo ≥ 80%.
- Warnings de deprecación en la suite: objetivo 0.

---

**¿Preguntas? Consultar en el canal #backend o revisar `MVP.md` / `TESTING.md`.**
