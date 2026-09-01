# Requisitos del Proyecto miIFTS

## Descripción
API backend para un Instituto de Formación Técnica Superior (IFTS) que gestiona usuarios, materias, recursos académicos, recordatorios y convenios/talentotech.

## Requisitos Funcionales

### Autenticación (auth)
- RF-01: Registro de usuarios con email único, nombre, contraseña hasheada (bcrypt) y rol (estudiante/admin).
- RF-02: Login con email/contraseña que devuelve JWT (HS256, 24h de expiración).
- RF-03: Obtener perfil del usuario autenticado (endpoint `/auth/me`).
- RF-04: Verificar validez de token JWT (`/auth/verify`).

### Materias (materias)
- RF-05: CRUD de carreras (nombre, duración, IFTS de referencia).
- RF-06: CRUD de materias por carrera (código único por carrera).
- RF-07: Gestión de correlativas (materia → materia prerequisito).
- RF-08: Gestión de cursadas (alta/modificación/eliminación de materias por usuario con notas).
- RF-09: Consulta de materias por usuario y cálculo de promedio.
- RF-10: Consulta de correlativas por materia.

### Recursos (recursos)
- RF-11: CRUD de recursos académicos (título, URL, descripción, materia).
- RF-12: Listar recursos por usuario o por materia.
- RF-13: CRUD de convenios interinstitucionales (institución, carrera destino, link).
- RF-14: CRUD de cursos TalentoTech (carrera, categoría, link de inscripción).
- RF-15: Listar convenios/talentotech por carrera o categoría.
- RF-16: Filtrar recursos por materia, tipo de archivo, rango de fechas. Ordenar por fecha_creacion o titulo.

### Recordatorios (recordatorios)
- RF-17: Crear recordatorios por usuario (título, fecha, tipo, materia opcional).
- RF-18: Listar recordatorios por usuario.
- RF-19: Eliminar recordatorios por usuario.
- RF-20: Buscar recordatorios por tipo, rango de fechas (desde/hasta), materia. Ordenar por fecha descendente.

### Búsqueda (materias)
- RF-21: Búsqueda de materias por texto libre (nombre, código) con filtros opcionales de año y cuatrimestre. Endpoint: `GET /materias/buscar?q=...&anio=...&cuatrimestre=...`

## Requisitos No Funcionales
- RNF-01: API RESTful con FastAPI, responses en JSON.
- RNF-02: Base de datos SQLAlchemy con SQLite (default) configurable a PostgreSQL.
- RNF-03: CORS configurable via variable de entorno `CORS_ORIGINS`.
- RNF-04: Categorización de errores HTTP (401, 404, 409, 500) consistente.
- RNF-05: Testing con pytest usando SQLite en memoria, sin base de datos real.
- RNF-06: Estructura de paquetes por feature (model, schema, repository, service, router, dependencies).
- RNF-07: Enmascaramiento de `password_hash` en respuestas JSON.
- RNF-08: Validación de schemas con Pydantic v2 (`from_attributes = True`).

## Restricciones
- Las contraseñas nunca se exponen en respuestas.
- El hash bcrypt está integrado en el servicio de auth.
- Los endpoints de recursos requieren autenticación para creación; otros recursos no tienen middleware de auth implementado aún (pendiente del sprint).
- `get_usuario_actual()` en materias/router.py retorna hardcodeo `1` — pendiente de reemplazo por JWT real.
- El modelo `Recurso` no tiene campo `tipo`. Se requiere agregarlo para soportar el filtrado RF-16.
- La búsqueda de materias (RF-21) usa un endpoint nuevo (`/materias/buscar`) que no existe aún.

## Fuentes Verificables
- `app/main.py` — rutas registradas, CORS configurado.
- `app/features/auth/` — endpoints de auth.
- `app/features/materias/router.py` — endpoints de carreras/materias/cursadas.
- `app/features/recursos/routers/` — endpoints de recursos/convenios/talentotech.
- `app/features/recordatorios/router.py` — endpoints de recordatorios.
- `requirements.txt` — dependencias.