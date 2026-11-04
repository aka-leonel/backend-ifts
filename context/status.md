# Estado Operativo Actual

## Fase: COMPLETE

## Feature activa
`talentotech` — N:M con carreras + `todas_las_carreras` (RF-37…RF-41, AC-15…AC-20, D20).
`convenios` — N:M sentó el patrón: RF-28…RF-36, AC-1…AC-14, D17.

## Próxima Acción
- Revisión final del Arquitecto (D20 + breaking change de contrato de TalentoTech).
- Commit de los cambios pendientes (14+ archivos sin commitear).

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
- `DATABASE_URL=sqlite:///./_pytest.db python -m pytest -q`: **312 passed, 1 skipped**
  (incluye 16 tests en `tests/test_talentotech.py`; se actualizaron 3 tests de
  autorización al contrato nuevo).
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

## TalentoTech (N:M + card)
- Mismo modelo que convenios: tabla intermedia `talentotech_carreras` + flag
  `todas_las_carreras`. Se agregaron `institucion`, `modalidad_cursada` (NOT NULL) y
  `dificultad` (nullable); se eliminó `carrera_id`.
- `TalentoTechResponse` ya no hereda de Create: expone `id`, `institucion`,
  `nombre_curso`, `categoria`, `descripcion`, `duracion`, `modalidad_cursada`,
  `dificultad`, `link_inscripcion`, `todas_las_carreras` y `carreras: CarreraResumen[]`.
- Unicidad `(institucion, nombre_curso)` → 409. Orden `lower(nombre_curso) ASC, id ASC`.
- Migración `e8b3c1d5f7a9` (down_revision `d4f6a1c9e2b7`), aplicada en SQLite local y en
  Postgres Docker (head). Seed `--talentotech` idempotente.
- Dato cargado en ambas bases: 1 curso ("Tecnologías Emergentes", Agencia de Habilidades
  para el Futuro, wildcard=true, 0 asociaciones, `modalidad_cursada="Virtual Asincrónico"`).
  Segunda corrida: insertados 0.
- `modalidad_cursada` confirmada por el usuario ("Virtual Asincrónico") y corregida en
  `seed.py`, `docs/DATA_TALENTOTECH.md`, `context/decisions.md` (D20) y en ambas bases
  (SQLite local y Postgres Docker); contenedor `api` recompilado (imagen con seed correcto).
- `carrera_ids` acepta una o varias carreras (igual que convenios): test de regresión
  `test_crear_con_varias_carreras` agregado.
- API: `GET /talentotech/` total=1, `modalidad_cursada="Virtual Asincrónico"`,
  `todas_las_carreras=true`, `carreras=[]`; `/carrera/1`, `/2`, `/3` → 1 cada una;
  `/carrera/99` → 0; `/categoria/IT` → 1.
- Docs: `docs/INTEGRACION_FRONT.md` (§3.4 + tipos TS), `docs/DATA_TALENTOTECH.md` (nuevo),
  `docs/openapi.json` regenerado (37 paths), `context/requirements.md` (RF-37…RF-41 /
  AC-15…AC-20), `context/decisions.md` (D20).
- Nuevo `docs/TALENTOTECH_FRONT.md`: contrato de API de TalentoTech para el agente del front
  (card completa, `carrera_ids`/`todas_las_carreras`, `PUT`, orden estable, formatos de 422/409);
  `docs/INTEGRACION_FRONT.md` §3.4 y `docs/DATA_TALENTOTECH.md` apuntan a ese documento.

## Blockers
- Ninguno.

## Notas
- Cambios sin commitear: todo queda en el working tree.
- Desvío de coordinación: el runtime bloqueó subagentes por límite de profundidad
  (`subagent_depth=1`), así que Planner implementó y validó directamente.
- `GET /convenios/carrera/{id}` devuelve vacío si la carrera no existe, aunque haya
  convenios wildcard (se preserva el contrato de arquitectura).
