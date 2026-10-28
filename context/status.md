# Estado Operativo Actual

## Fase: COMPLETE

## Feature activa
`convenios` — N:M con carreras de origen + `todas_las_carreras` (RF-28…RF-36, AC-1…AC-14, D17).

## Próxima Acción
- Confirmación del usuario del `link_info` del nuevo convenio UNLZ *Gestión de Sistemas de
  Automatización y Robótica* (se usó la página de oferta de UNLZ).
- Revisión final del Arquitecto (breaking change de contrato + D18/D19).

## Tasks

| Task ID | Descripción | Estado | Dependencias |
|---------|-------------|--------|--------------|
| CONV2-001 | Modelo N:M + migración Alembic `d4f6a1c9e2b7` | Completada | — |
| CONV2-002 | Schemas del contrato nuevo | Completada | — |
| CONV2-003 | Repository + Service + Router | Completada | CONV2-001, CONV2-002 |
| CONV2-004 | Seed `carrera_ids` / `todas_las_carreras` | Completada | CONV2-001 |
| CONV2-005 | Tests AC-1…AC-14 + regresión | Completada | CONV2-003, CONV2-004 |
| CONV2-006 | Docs + `openapi.json` | Completada | CONV2-003 |

## Validación (evidencia)
- `DATABASE_URL=sqlite:///./_pytest.db python -m pytest -q`: **296 passed, 1 skipped**.
- `tests/test_convenios.py`: **33 passed** (M2M, wildcard, PATCH ids/flag, invariantes,
  ids inexistentes, duplicado, dedupe, orden, búsqueda, paginación sin duplicados,
  carreras ordenadas por nombre, delete de intermedia). Incluye
  `test_orden_institucion_es_case_insensitive` (D19).
- Alembic sobre SQLite: `upgrade b7d2f8c41a30` con datos → `upgrade head` copia
  `convenios_carreras` (2/2 filas), crea flag/unique nueva, dropea columna e índice;
  `downgrade -1` restaura `carrera_id` + unique vieja + índice; `upgrade head` OK.
  Con duplicados `(institucion, carrera_destino)` el upgrade aborta con `RuntimeError`
  accionable.
- Seed: `python seed.py` (0 convenios) y `python seed.py --convenios` (2 veces) OK.
  Prueba en memoria con datos ficticios: inserta M2M + wildcard, segunda corrida inserta 0,
  flag+ids inválido lanza `ValueError` claro.
- `docs/openapi.json` regenerado (37 paths) con `ConvenioCreate/Update/Response` y
  `CarreraResumen` nuevos.

## Carga de datos (convenios)
- 10 convenios del usuario cargados: SQLite local `miifts.db` (10 convenios, 8 filas
  `convenios_carreras`, 5 wildcard) y Postgres del stack Docker (10, 8 y 5).
- Correcciones de datos aplicadas en ambas bases:
  - Videojuegos: `link_info` corregido a
    `https://www.udelaciudad.edu.ar/licenciatura-en-desarrollo-y-produccion-de-videojuegos`.
  - "Universidad de la Ciudad de Buenos Aires" (antes "Cuidad").
  - "Universidad Nacional de Lanús" (antes "Lanus").
  - UNLZ *Licenciatura en Gestión de la Información*: carreras de origen `[2,3]` (antes `[1,3]`).
  - Nuevo convenio UNLZ *Gestión de Sistemas de Automatización y Robótica* para carreras
    `[1,3]`, sin `link_info` propio: se usó la misma página de oferta de UNLZ
    (`https://ingenieria.unlz.edu.ar/oferta-academica/grado#licenciaturas`), pendiente de
    confirmación del usuario.
- Orden de convenios case-insensitive: `lower(institucion) ASC, id ASC` (D19).
- Admin en Postgres: `admin@miifts.ar` / `admin1234` (rol ADMIN, id=4), vía
  `python seed.py --admin` (flag idempotente).
- Idempotencia en ambas bases: 2ª corrida de `python seed.py --convenios` →
  "insertados: 0, ya existían: 10".
- Migraciones en Postgres hasta head `d4f6a1c9e2b7` (entrypoint del contenedor ejecuta
  `alembic upgrade head`).
- Catálogo de carreras de Postgres estaba obsoleto (ids 1 y 2 ambos "Desarrollo de
  Software", sin id 3); normalizado de forma no destructiva a los ids 1/2/3 del seed
  canónico (D18). No se borraron usuarios ni otras tablas.
- API `localhost:8000`: `GET /convenios/` total=10; `/convenios/carrera/1`=7, `/2`=8 y
  `/3`=8; carrera 99 total=0; login admin OK; `?q=videojuegos` total=1.
- Entregable `docs/DATA_CONVENIOS.md` (JSON + seed, comandos local/Postgres/API,
  verificación y notas).

## Blockers
- Ninguno.

## Notas
- Cambios sin commitear: todo queda en el working tree.
- Desvío de coordinación: el runtime bloqueó subagentes por límite de profundidad
  (`subagent_depth=1`), así que Planner implementó y validó directamente.
- `GET /convenios/carrera/{id}` devuelve vacío si la carrera no existe, aunque haya
  convenios wildcard (se preserva el contrato de arquitectura).
