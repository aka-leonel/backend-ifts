# Convenios + TalentoTech - Backend

## Endpoints

### Convenios (`/convenios`)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/convenios/` | ❌ | Lista paginada |
| GET | `/convenios/carrera/{id}` | ❌ | Por carrera (paginado) |
| GET | `/convenios/{id}` | ❌ | Detalle |
| POST | `/convenios/` | ✅ Admin | Crea (institucion, carrera_destino, descripcion, link_info, carrera_id) |
| PUT | `/convenios/{id}` | ✅ Admin | Actualiza |
| DELETE | `/convenios/{id}` | ✅ Admin | Elimina |

### TalentoTech (`/talentotech`)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/talentotech/` | ❌ | Lista paginada |
| GET | `/talentotech/carrera/{id}` | ❌ | Por carrera (paginado) |
| GET | `/talentotech/categoria/{cat}` | ❌ | Por categoría exact match (paginado) |
| GET | `/talentotech/{id}` | ❌ | Detalle |
| POST | `/talentotech/` | ✅ Admin | Crea (nombre_curso, categoria, descripcion, duracion, link_inscripcion, carrera_id) |
| PUT | `/talentotech/{id}` | ✅ Admin | Actualiza |
| DELETE | `/talentotech/{id}` | ✅ Admin | Elimina |

## Modelos

```python
# Convenio
id, carrera_id(FK), institucion(150), carrera_destino(150), descripcion, link_info(URL)

# TalentoTech
id, carrera_id(FK), nombre_curso(150), categoria(20), descripcion, duracion(50), link_inscripcion(URL)
```

## Services

**ConvenioService:** `get_all_paginado`, `get_by_carrera_paginado`, `get_by_id`, `create`, `update`, `delete` (valida existe + repo)

**TalentoTechService:** `get_all_paginado`, `get_by_carrera_paginado`, `get_by_categoria_paginado`, `get_by_id`, `create`, `update`, `delete`

## Routers

- `routers/convenios.py`: GET `/`, `/carrera/{id}`, `/{id}` (público); POST/PUT/DELETE (require_admin)
- `routers/talentotech.py`: GET `/`, `/carrera/{id}`, `/categoria/{cat}`, `/{id}` (público); POST/PUT/DELETE (require_admin)

## Dependencias

```python
get_convenio_service(db) → ConvenioService(ConvenioRepository(db))
get_talentotech_service(db) → TalentoTechService(TalentoTechRepository(db))
```

## Validaciones

| Regla | Implementación |
|-------|----------------|
| `link_info` / `link_inscripcion` URL válida | `HttpUrl` en Pydantic |
| `categoria` TalentoTech | String(20) libre; frontend sugiere opciones |
| `duracion` TalentoTech | String(50) libre (ej: "3 meses") |
| Admin only write | `require_admin` dependency |
| Lectura pública | GET sin auth |
| Paginación | `PaginatedResponse` en todos los GET listados |

## Errores

| Código | Endpoints | Causa |
|--------|-----------|-------|
| 401 | POST/PUT/DELETE | No autenticado |
| 403 | POST/PUT/DELETE | No es admin |
| 404 | GET by ID, PUT, DELETE | Recurso no existe |
| 422 | POST/PUT | Validación (URL inválida, campos requeridos) |