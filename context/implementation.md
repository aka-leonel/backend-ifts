# Plan de Implementación: Convenios — N:M con carreras de origen + `todas_las_carreras`

## Objetivo
Cumplir RF-28…RF-36 (AC-1…AC-14) reemplazando `convenios.carrera_id` por la relación N:M
`convenios_carreras` + flag `convenios.todas_las_carreras`, según D17 (decisión cerrada).
Breaking change aceptado: no hay datos ni cliente en producción. **No se inventan convenios**:
`CONVENIOS_SEED` queda vacío hasta que el usuario provea los datos.

## Alcance
- Backend FastAPI/SQLAlchemy/Alembic: feature `recursos`/`convenios`, migración, `seed.py`,
  tests, docs de integración y `docs/openapi.json`.
- Fuera de alcance: TalentoTech, notificaciones, otras features, dependencias nuevas.

## Referencias
- Requisitos: RF-28…RF-36 / AC-1…AC-14 (`context/requirements.md`).
- Decisión: D17 (`context/decisions.md`).
- Arquitectura: «Convenios — contrato vigente» (`context/architecture.md`).

---

## Desglose de Tasks

### Task CONV2-001: Modelo N:M + migración Alembic
**Objetivo:** nueva representación de datos y migración reversible con copia de datos existentes.
**Componentes:** `app/features/recursos/model.py`,
`alembic/versions/<nueva>_convenios_carreras_m2m.py`.
**Detalle:**
- `Convenio`: quitar `carrera_id`; agregar `todas_las_carreras = Column(Boolean, nullable=False,
  default=False, server_default=text("false"))`; unique `uq_convenios_institucion_destino`
  sobre `(institucion, carrera_destino)`; relación
  `carreras = relationship("Carrera", secondary="convenios_carreras", lazy="selectin",
  order_by="Carrera.nombre")`.
- `ConvenioCarrera` (`convenios_carreras`): `convenio_id` FK `convenios.id` `ondelete="CASCADE"`,
  `carrera_id` FK `carreras.id`, PK compuesta.
- Migración manual (`down_revision = 'b7d2f8c41a30'`), sin autogenerate:
  crear tabla intermedia → `INSERT ... SELECT id, carrera_id FROM convenios` → agregar flag
  (NOT NULL, server_default false) → `batch_alter_table`: drop unique vieja
  `uq_convenios_carrera_institucion_destino`, crear `uq_convenios_institucion_destino`,
  drop índice `ix_convenios_carrera_id` si existe, drop columna `carrera_id`.
- `downgrade()`: recrear columna `carrera_id` (tomar una carrera asociada por convenio, o la
  primera carrera si quedó wildcard), recrear la unique vieja, borrar tabla intermedia y flag.
- Funciona en SQLite (batch) y PostgreSQL; `Base.metadata.create_all` debe crear ambas tablas.

### Task CONV2-002: Schemas del contrato nuevo
**Componentes:** `app/features/recursos/schema.py`, `app/features/recursos/__init__.py`.
**Detalle:**
- `ConvenioCreate`: `institucion`, `carrera_destino`, `descripcion`, `link_info` (HttpUrl),
  `carrera_ids: list[int] | None = None`, `todas_las_carreras: bool = False`; `strip()` en textos.
- `ConvenioUpdate`: mismos campos opcionales (incluye `carrera_ids`, `todas_las_carreras`).
- `CarreraResumen` (`id`, `nombre`, `from_attributes=True`).
- `ConvenioResponse` sin herencia de `ConvenioCreate`: `id`, `institucion`, `carrera_destino`,
  `descripcion`, `link_info`, `todas_las_carreras`, `carreras: list[CarreraResumen]`;
  `from_attributes=True`.
- Exportar `CarreraResumen` en `__init__.py`.

### Task CONV2-003: Repository + Service + Router
**Componentes:** `app/features/recursos/repository.py`, `service.py`, `routers/convenios.py`.
**Detalle repository:**
- `query_by_carrera`: `or_(Convenio.todas_las_carreras.is_(True),
  Convenio.carreras.any(Carrera.id == carrera_id))` + `q` + orden; sin duplicados ni romper `count()`.
- `get_by_unique_key(institucion, carrera_destino, exclude_id)`.
- `carreras_existentes(ids) -> set[int]`.
- `create_convenio(convenio, carreras)`, `update_convenio(id, ...)` (reemplazo total),
  `update_convenio_parcial(id, datos)` (sincroniza lista), `delete_convenio` (limpia intermedia
  explícitamente si hace falta).
**Detalle service:**
- `_validar_carreras(ids)`: deduplicar preservando orden; faltantes → `DomainValidationError` 422
  con `"No existen las carreras: 4, 7"` (singular si es una); lista vacía con flag false → 422.
- Invariante flag↔ids en create/update/patch; `true` ⇒ no se guardan filas.
- Unicidad `(institucion, carrera_destino)` en create/update/patch → `DuplicateError` 409.
- PATCH combina con estado actual; `carrera_ids` presente reemplaza; body vacío → 200; `null` se ignora.
- GET sin cambios funcionales.
**Detalle router:** sin cambios de paths/semántica; solo recibe los schemas nuevos.

### Task CONV2-004: Seed
**Componentes:** `seed.py`.
**Detalle:**
- Formato canónico: `institucion`, `carrera_destino`, `descripcion`, `link_info` + `carrera_ids`
  **o** `todas_las_carreras: true`.
- `_insertar_convenios`: resolver/validar ids contra `Carrera`, insertar convenio + filas de la
  intermedia, idempotencia por `(institucion, carrera_destino)`, mensajes claros con ids disponibles.
- `python seed.py --convenios` sigue funcionando sin borrar nada.
- Lista `CONVENIOS_SEED` VACÍA + comentario de formato actualizado.

### Task CONV2-005: Tests
**Componentes:** `tests/test_convenios.py`, ajustes en `test_estructura_respuestas.py` /
`test_authorization.py` si dependen de `carrera_id`.
**Escenarios:** M2M (carrera 1 y 2, no 3), wildcard (`carreras=[]`), PATCH de ids, PATCH flag true
limpia intermedia, PATCH flag false sin ids → 422, POST flag true + ids → 422, ids inexistentes →
422 con lista, duplicado por (institucion, destino) con carreras distintas → 409, dedupe, orden,
búsqueda, paginación por carrera sin duplicados, `carreras` ordenadas por nombre.

### Task CONV2-006: Docs
**Componentes:** `docs/CONVENIOS_FRONT.md` (reescritura), `docs/INTEGRACION_FRONT.md` §3.4 y §5,
`api-requests.http` sección CONVENIOS, `docs/openapi.json` regenerado con
`python scripts/export_openapi.py`.

---

## Dependencias y orden
```
CONV2-001 (modelo+migración) ─┐
CONV2-002 (schemas) ──────────┼→ CONV2-003 (repo/service/router) → CONV2-004 (seed)
                              └→ CONV2-005 (tests) ← CONV2-003, CONV2-004
CONV2-006 (docs/openapi) ← CONV2-003
```
Ejecución: 001+002 → 003 → 004+005 → 006 → validación Tester.

## Restricciones de ejecución
- Sin dependencias nuevas; no tocar TalentoTech ni otras features (solo leer `Carrera`).
- Mantener `PaginatedResponse`, `?q=`, orden `institucion ASC, id ASC`, `strip()` y unicidad
  case-sensitive.
- Migración sin autogenerate y reversible; no basar tests de integridad en FKs de SQLite.
- No commitear DBs temporales ni datos de convenios inventados.

## Riesgos
| Riesgo | Mitigación |
|---|---|
| `count()`/`EXISTS` duplica filas en listado por carrera | usar `Convenio.carreras.any(...)` (subconsulta EXISTS) |
| SQLite no soporta DROP COLUMN/CONSTRAINT | `batch_alter_table` en la migración |
| `selectin` en relación + refresh | verificar serialización `carreras` en respuesta |
| Wildcard + `carrera_ids` | validación de invariante en service (422) |
| Sin PostgreSQL/Docker | validar upgrade/downgrade/upgrade en SQLite |
