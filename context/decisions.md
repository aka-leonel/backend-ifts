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