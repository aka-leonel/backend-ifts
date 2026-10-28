# Decisiones Arquitectónicas del Proyecto miIFTS

## D01: Framework FastAPI + SQLAlchemy para el ORM
- **Context**: Proyecto backend académico que requiere API REST con autenticación y gestión de datos relacionales.
- **Decisión**: Usar FastAPI como framework web y SQLAlchemy 2.0 como ORM.
- **Alternativas consideradas**: Flask, Django REST Framework, Tortoise ORM.
- **Rationale**: FastAPI ofrece validación automática de schemas con Pydantic, documentación OpenAPI nativa y alto rendimiento. SQLAlchemy 2.0 es el ORM maduro estándar en Python.
- **Consecuencias**: Dependencia de `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`. La estructura de 4 capas por feature se alinea naturalmente con FastAPI.

## D02: Base de datos SQLite como default con opción PostgreSQL
- **Context**: Entorno de desarrollo y testing necesita ser rápido y sin dependencias externas.
- **Decisión**: SQLite como default (`sqlite:///./miifts.db`), configurable a PostgreSQL via `DATABASE_URL`.
- **Alternativas**: Solo PostgreSQL, solo SQLite.
- **Rationale**: SQLite elimina infraestructura para desarrollo/testing. La variable de entorno permite PostgreSQL en producción. El `check_same_thread=False` habilita threading en SQLite.
- **Consecuencias**: `DATABASE_URL` es la única configuración de DB. Tests usan SQLite en memoria independiente.

## D03: Autenticación JWT con python-jose + bcrypt
- **Context**: Se necesita autenticación stateless con roles.
- **Decisión**: JWT (HS256) con `python-jose` para tokens y `passlib/bcrypt` para hashing.
- **Alternativas**: Tokens de sesión, OAuth2 completo con proveedor externo.
- **Rationale**: JWT stateless es adecuado para SPA frontend (CORS configurado). bcrypt es el estándar para hashing de contraseñas.
- **Consecuencias**: `SECRET_KEY` sensible, debe estar en `.env`. Tokens de 24h de expiración. `OAuth2PasswordBearer` para extraer token del header.

## D04: Patrón 4 capas por feature (model/schema/repository/service + router)
- **Context**: Múltiples features con lógica de negocio y acceso a datos.
- **Decisión**: Cada feature tiene model (SQLAlchemy), schema (Pydantic), repository (CRUD), service (lógica) y router (endpoints).
- **Alternativas**: Capa única monolítica, CQRS, hexagonal architecture.
- **Rationale**: Separación clara de responsabilidades, testeable en cada capa, consistente entre features.
- **Consecuencias**: Flujo `Router → Service → Repository → DB` uniforme. Los servicios levantan excepciones personalizadas que los routers capturan y convierten a HTTP status codes.

## D05: Estructura de paquetes por feature en `app/features/`
- **Context**: Organización del código fuente.
- **Decisión**: `app/features/{nombre}/` por dominio, con `app/shared/` como carpeta reservada (actualmente vacía).
- **Alternativas**: Capas horizontales (`app/models/`, `app/services/`, `app/routers/`), dominio por carpeta con subcapas.
- **Rationale**: Co-localización de todo lo relacionado a un dominio. Fácil de navegar y escalar.
- **Consecuencias**: `app/shared/` (models, schemas, utils) está reservado pero no se usa aún. Los routers de recursos se subdividen en `routers/` dado su volumen.

## D06: Testing con pytest + SQLite en memoria + FastAPI TestClient
- **Context**: Necesidad de tests rápidos e aislados sin base de datos real.
- **Decisión**: pytest con fixtures en `tests/conftest.py`, SQLite `:memory:` con `StaticPool`, `TestClient` con `dependency_overrides`.
- **Alternativas**: factory_boy, mocks completos, base de datos de test separada.
- **Rationale**: `StaticPool` permite que todas las sesiones compartan la misma conexión en memoria. Los `dependency_overrides` reemplazan `get_db` sin modificar código de producción.
- **Consecuencias**: Tests completamente aislados. Fixtures reutilizables (`client`, `db_session`, `carrera_test`, `auth_headers`). Tests marcados como `xfail` para funcionalidad pendiente.

## D07: Pydantic v2 con `from_attributes = True`
- **Context**: Necesidad de mapeo ORM → schema.
- **Decisión**: Pydantic v2 con `Config.from_attributes = True` (reemplazo de `orm_mode = True` de v1).
- **Alternativas**: Serialización manual, `@model_validator`.
- **Rationale**: Permite `UsuarioResponse.model_validate(usuario_db)` directamente. Código limpio y mantenible.
- **Consecuencias**: Todos los schemas de respuesta usan esta configuración. Compatibilidad con SQLAlchemy models.

## D08: Excepciones personalizadas en servicios, HTTP errors en routers
- **Context**: Separar lógica de negocio de la capa de presentación HTTP.
- **Decisión**: Los servicios levantan excepciones Python normales (`RecursoNotFound`, `ConvenioNotFound`, `MateriaYaCargada`). Los routers las capturan y devuelven HTTP status codes.
- **Alternativas**: HTTPException directa en el servicio, clase base de exception con handler global.
- **Rationale**: Los servicios son reutilizables sin dependencia de FastAPI. Los routers controlan la semántica HTTP.
- **Consecuencias**: Cada servicio define sus excepciones. Los routers tienen try/except para cada excepción.

## D09: Agregar campo `tipo` al modelo Recurso para filtrado por tipo de archivo
- **Context**: El requisito RF-16 pide filtrar recursos por `tipo=pdf`. El modelo `Recurso` actual no tiene campo `tipo`.
- **Decisión**: Agregar columna `tipo` (String, nullable=True) al modelo `Recurso` en `app/features/recursos/model.py`.
- **Alternativas**:
  - Derivar el tipo de la extensión de la URL (complejo, frágil, acoplado al formato de URL).
  - No agregar campo y usar solo `titulo` y `descripcion` en la búsqueda de texto (no cumple el requisito).
- **Rationale**: Un campo explícito `tipo` permite filtrado preciso, consistente con el patrón de otros campos del modelo. Es el enfoque más simple y mantenible.
- **Consecuencias**: Requiere migration de Alembic (o `Base.metadata.drop_all()` + `create_all()` en desarrollo). El schema `RecursoCreate` y `RecursoResponse` necesitan actualizar el campo `tipo`. El servicio y repository deben soportar el filtro.

## D10: Nuevo endpoint `GET /materias/buscar` para búsqueda de materias
- **Context**: El requisito RF-21 pide un endpoint de búsqueda de materias con texto libre y filtros opcionales. No existe endpoint similar en `materias/router.py`.
- **Decisión**: Agregar un nuevo endpoint `GET /materias/buscar` con query params `q`, `anio`, `cuatrimestre`. Implementar en service y repository de materias.
- **Alternativas**:
  - Agregar filtros al endpoint `GET /materias/` existente (cambiar firma, puede romper compatibilidad).
  - Crear endpoint separado `/materias/buscar` (más explícito, sigue el principio de responsabilidad única).
- **Rationale**: Un endpoint dedicado es más claro y semántico. La búsqueda es un patrón de acceso distinto del listado por carrera.
- **Consecuencias**: Nuevo método en `MateriaRepository` (query con filtros dinámicos). Nueva función en `service.py` de materias. Nuevo schema de respuesta o reutilización de `MateriaResponse`.

## D11: Búsqueda de recordatorios con filtros dinámicos y ordenamiento
- **Context**: El requisito RF-20 pide filtrar recordatorios por tipo, rango de fechas (desde/hasta), materia, y ordenar por fecha descendente. El endpoint actual `GET /recordatorios` solo acepta `usuario_id`.
- **Decisión**: Extender el endpoint `GET /recordatorios` para aceptar query params opcionales: `tipo`, `desde`, `hasta`, `materia_id`. Agregar ordenamiento por fecha descendente por defecto.
- **Alternativas**:
  - Crear un endpoint `/recordatorios/buscar` separado.
  - Extender el endpoint existente (menos endpoint, más simple si es el mismo recurso).
- **Rationale**: La búsqueda es una variante del listado por usuario, con filtros adicionales. Extender el endpoint existente evita duplicación de ruta y mantiene la convención de `/recordatorios?usuario_id=1&tipo=examen&...`.
- **Consecuencias**: El service de recordatorios necesita aceptar filtros opcionales. El repository necesita construir queries dinámicos. El schema de query necesita definirse.

## D12: Convenios — validación de `carrera_id` con 422 (no 404/409)
- **Context**: Un `POST /convenios/` con `carrera_id` inexistente llegaba a la DB y terminaba en `IntegrityError` → handler global 409 genérico. En SQLite las FK no se fuerzan, por lo que además se podían crear convenios huérfanos.
- **Decisión**: Validar la existencia de la carrera en la capa de **servicio** antes de escribir y lanzar `DomainValidationError` (422) con mensaje explícito (`No existe la carrera {id}`). Aplica a POST, PUT y PATCH (solo si `carrera_id` viene en el body).
- **Alternativas**: `404` (se confunde con "convenio inexistente", que es el recurso de la ruta); seguir usando `BadRequestError` 400 (menos preciso semánticamente); delegar solo en la FK de Postgres (no funciona en SQLite y devuelve 409 genérico).
- **Rationale**: El error es un dato inválido del body, no un recurso de la ruta inexistente. `422` es coherente con `DomainValidationError` y con la validación Pydantic. Es portable entre SQLite y PostgreSQL.
- **Consecuencias**: `ConvenioService` necesita acceso a la tabla `carreras` (método en `ConvenioRepository` reutilizando `Carrera` o inyección de `CarreraRepository`). Un único punto de validación para create/update. `GET` no cambia.

## D13: Convenios — unicidad por `(carrera_id, institucion, carrera_destino)`
- **Context**: No existía ninguna restricción; dos POST idénticos creaban duplicados.
- **Decisión**: Agregar `UniqueConstraint("carrera_id", "institucion", "carrera_destino")` en el modelo + migración Alembic. El service verifica duplicados antes de escribir y lanza `DuplicateError` (409); se mantiene el handler global de `IntegrityError` como red de seguridad para carreras concurrentes.
- **Alternativas**: Unicidad solo por `institucion` (demasiado restrictiva: una institución puede tener convenios con varias carreras destino); unicidad case-insensitive con índice funcional (complejidad y diferencias SQLite/Postgres); sin constraint y solo chequeo en service (no protege concurrencia ni datos cargados por seed).
- **Rationale**: La combinación identifica naturalmente un convenio y evita duplicados sin impedir casos legítimos. Es portable entre SQLite y PostgreSQL.
- **Consecuencias**: Migración nueva sobre `convenios`. Los textos se normalizan con `strip()` en los schemas para que " X " y "X" cuenten como iguales. La comparación es case-sensitive (se documenta). Risco: si una DB existente tuviera duplicados, la migración falla; la DB de desarrollo está vacía (0 convenios), así que no aplica hoy.

## D14: Convenios — orden estable `institucion ASC, id ASC`
- **Context**: Los listados paginaban sin `ORDER BY`; el orden dependía del plan de la DB y podía repetir/omitir filas entre páginas.
- **Decisión**: Ordenar **todos** los listados de convenios (`/convenios/` y `/convenios/carrera/{id}`) por `institucion ASC, id ASC`, aplicado en el repository antes de paginar.
- **Alternativas**: `ORDER BY id` (estable pero poco útil para el usuario); orden configurable por query param (fuera de alcance, superficie innecesaria).
- **Rationale**: Orden alfabético por institución es lo esperable en una pantalla de convenios; `id` como desempate garantiza determinismo total.
- **Consecuencias**: `paginate()` no cambia; el `query_*` correspondiente devuelve el orden ya aplicado. No rompe contrato (solo cambia el orden observable).

## D15: Convenios — búsqueda por texto con `?q=`
- **Context**: No había forma de buscar convenios por institución ni texto.
- **Decisión**: Agregar query param opcional `q` a `GET /convenios/` y `GET /convenios/carrera/{carrera_id}`. Filtra con `ILIKE %q%` sobre `institucion`, `carrera_destino` y `descripcion` (OR). `q` vacío/ausente no filtra. Se aplica antes de paginar.
- **Alternativas**: Endpoint `/convenios/buscar` dedicado (más superficie para el mismo recurso); parámetros separados `institucion=` y `texto=` (peor UX y más combinaciones).
- **Rationale**: Sigue el patrón ya usado en `/materias/buscar` (`ilike`), es retrocompatible y una sola caja de búsqueda en el front cubre institución + destino + descripción.
- **Consecuencias**: `query_all`/`query_by_carrera` reciben `q: Optional[str]`. Sin cambios en el schema de respuesta ni en paginación.

## D16: Convenios — `PATCH` parcial y `PUT` conservado
- **Context**: `PUT /convenios/{id}` exigía los 5 campos; editar uno solo obligaba a reenviar todo.
- **Decisión**: Agregar `PATCH /convenios/{id}` (admin) con schema `ConvenioUpdate` (todos los campos `Optional`), aplicando solo los campos presentes (`model_dump(exclude_unset=True)`). `PUT` se mantiene con semántica de reemplazo total por compatibilidad.
- **Alternativas**: Reemplazar `PUT` por `PATCH` (rompe clientes y tests existentes); hacer `PUT` parcial (contradice la semántica HTTP y confunde).
- **Rationale**: `PATCH` es la semántica correcta para edición parcial y el front solo manda lo que cambia. Mantener `PUT` evita regresiones.
- **Consecuencias**: El service necesita una operación de actualización parcial; las validaciones (carrera existente, unicidad) se ejecutan solo sobre los campos presentes, combinándolos con el estado actual para chequear colisiones. Body vacío devuelve el convenio sin cambios (200).

## D17: Convenios — relación N:M con carreras de origen + flag `todas_las_carreras`
- **Context**: Un mismo convenio (institución + carrera destino) puede estar disponible para egresados de **varias** carreras de origen. El modelo anterior (`convenios.carrera_id` + unique por carrera) solo lo representaba duplicando filas, lo que rompe paginación, totales, búsqueda, detalle y edición consistente. Además se necesita expresar "aplica a todas las carreras".
- **Decisión**:
  - Quitar `carrera_id` de `convenios`.
  - Agregar `convenios_carreras (convenio_id, carrera_id)` con PK compuesta y `ON DELETE CASCADE`.
  - Agregar `convenios.todas_las_carreras BOOLEAN NOT NULL DEFAULT false`.
  - Unicidad del convenio: `(institucion, carrera_destino)` (reemplaza la anterior).
  - Invariante: `todas_las_carreras = true` ⇒ sin filas en `convenios_carreras` y sin `carrera_ids` en el request; `false` ⇒ al menos una carrera.
  - Contrato: request `carrera_ids: int[]` (mín. 1, deduplicado) o `todas_las_carreras: true`; response `todas_las_carreras: bool` + `carreras: [{id, nombre}]` (vacío si es wildcard).
  - `GET /convenios/carrera/{id}` = asociaciones explícitas **OR** `todas_las_carreras`.
  - `PATCH`: `carrera_ids` reemplaza el conjunto completo; pasar a `true` limpia las filas de la tabla intermedia; pasar a `false` exige un conjunto no vacío resultante.
- **Alternativas**:
  - **Agrupar en el front** filas duplicadas: descartado. Rompe paginación/totales (`total` cuenta filas, no convenios), deja ids ambiguos para el detalle, exige N ediciones para un cambio y traslada la consistencia a un cliente no confiable.
  - **Columna `carreras_ids` como array/JSON**: no relacional, sin FK, no consultable con SQL estándar ni portable entre SQLite/PostgreSQL. Descartado.
  - **Solo flag, sin N:M**: no permite "disponible para 1 y 2, pero no 3". Descartado.
  - **Flag `todas_las_carreras` en lugar de listar siempre todas**: elegido porque no requiere mantener filas cuando se agrega una carrera nueva y expresa la intención del dominio.
- **Rationale**: Es la representación normalizada de una relación N:M real, con integridad referencial, consultas y paginación correctas. El flag evita mantenimiento manual del caso "todas". El momento es óptimo: la tabla no tiene datos.
- **Consecuencias**:
  - Es un **cambio incompatible** del contrato de convenios (`carrera_id` desaparece). Aceptable porque no hay datos ni cliente en producción; se actualiza `docs/CONVENIOS_FRONT.md` y `docs/openapi.json`.
  - Migración nueva (head `b7d2f8c41a30`): crear tabla intermedia, copiar `carrera_id` existentes, agregar flag, cambiar unique y dropear la columna.
  - `ConvenioResponse` deja de heredar de `ConvenioCreate` (el request usa `carrera_ids`, la respuesta `carreras`).
  - La consulta por carrera usa `EXISTS`/`any()` para no duplicar filas ni romper el conteo paginado.
  - El seed debe aceptar `carrera_ids` o `todas_las_carreras`.
  - Riesgo: carreras borradas dejan de aplicar; con CASCADE se limpian las filas de la intermedia, pero no se puede borrar una carrera mientras tenga convenios explícitos (FK).
  - `Carrera` sigue siendo texto libre en `carrera_destino`; la unicidad depende de la grafía exacta (case-sensitive, `strip()` aplicado).

## D18: Normalización no destructiva del catálogo de carreras en Postgres (dev)
- **Context**: La base Postgres de Docker estaba en la revisión `e763065820f1` con un catálogo obsoleto: dos carreras con el mismo nombre (`Desarrollo de Software`, ids 1 y 2), sin id 3, y dos usuarios que referencian las carreras 1 y 2. La data de convenios provista referencia los ids 1/2/3 del seed canónico (Desarrollo de Software, Análisis de Sistemas, Ciencia de Datos e IA).
- **Decisión**: Alinear el catálogo sin borrar datos: renombrar id 1 → *Tecnicatura Superior en Desarrollo de Software*, id 2 → *Tecnicatura Superior en Análisis de Sistemas* e insertar id 3 → *Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial*.
- **Alternativas**:
  - **`python seed.py` completo**: descartado; dropea todas las tablas y elimina usuarios/datos existentes.
  - **Mapear la data a los ids existentes**: descartado; el id 3 no existía y los ids 1/2 eran duplicados, por lo que las asociaciones habrían quedado semánticamente incorrectas.
  - **Dejar el catálogo como estaba**: descartado; el front mostraría dos carreras homónimas y no se podría cargar el convenio de Ciencia de Datos.
- **Rationale**: Es la opción mínima que hace coherente el catálogo con el seed y con la data, sin perder usuarios ni filas de otras tablas.
- **Consecuencias**:
  - El usuario id 2 (Ana) pasa a mostrarse en *Análisis de Sistemas* (antes *Desarrollo de Software*); su `carrera_id` no cambia.
  - Solo se tocó `carreras`; usuarios, IFTS y demás tablas quedan intactos.
  - Queda documentado en `docs/DATA_CONVENIOS.md` §6. Es una operación de datos de entorno de desarrollo, no una migración de esquema.

## D19: Convenios — orden alfabético case-insensitive
- **Context**: D14 definía `ORDER BY institucion ASC, id ASC`. Con la colación de SQLite/Postgres (case-sensitive) los nombres que empiezan con mayúscula se agrupan antes que los que siguen con minúscula, produciendo un orden poco natural: "Universidad **N**acional…" aparecía antes que "Universidad **d**e…".
- **Decisión**: Ordenar por `lower(institucion) ASC, id ASC` (D14 se mantiene en cuanto a desempate por `id`).
- **Alternativas**:
  - **Colación `NOCASE`/ICU por columna**: específica de cada motor y requiere migración; descartado por portabilidad SQLite/Postgres.
  - **Normalizar `institucion` a minúsculas al guardar**: cambia el dato mostrado; descartado.
- **Rationale**: `lower()` es portable, no altera los datos y da el orden esperado por un usuario hispanohablante.
- **Consecuencias**:
  - Cambia el orden observable del listado y de `GET /convenios/carrera/{id}`.
  - Se agregó un test de regresión (`test_orden_institucion_es_case_insensitive`).
  - Sigue siendo un orden determinista y estable (desempate por `id`).