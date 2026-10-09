# Recursos - Backend

## Endpoints

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/recursos/` | ❌ | Lista global con filtros + paginación |
| GET | `/recursos/{id}` | ❌ | Detalle |
| POST | `/recursos/` | ✅ Usuario | Crea (asocia `usuario_id` del token) |
| PUT | `/recursos/{id}` | ✅ Dueño | Actualiza (403 si ajeno) |
| DELETE | `/recursos/{id}` | ✅ Dueño | Elimina (403 si ajeno) |
| GET | `/recursos/usuario/{id}` | ❌ | Por usuario (paginado) |
| GET | `/recursos/materia/{id}` | ❌ | Por materia (paginado) |

## Filtros (GET `/recursos/`)

`materia_id`, `tipo` (exacto), `desde` (date), `hasta` (date), `page`, `per_page`  
Orden: `fecha_creacion DESC`

## Modelo

```python
Recurso: id, usuario_id(FK), materia_id(FK), titulo(150), url, descripcion, tipo(nullable), fecha_creacion
```
> Campo `tipo` agregado para RF-16 (valores: pdf, video, link, documento, otro)

## Service (`RecursoService`)

- `get_recursos_filtrados_paginado(materia_id, tipo, desde, hasta, params)` → query dinámica + paginate
- `get_by_usuario_paginado(usuario_id, params)` / `get_by_materia_paginado(materia_id, params)`
- `create(recurso, usuario_id)` → repo.create
- `update(id, recurso)` → valida existe → repo.update
- `delete(id)` → valida existe → repo.delete
- `get_by_id(id)` → 404 si no existe

## Repository

- `query_filtered(materia_id, tipo, desde, hasta)` → filtros opcionales + `order_by(fecha_creacion.desc())`
- `query_by_usuario(usuario_id)` / `query_by_materia(materia_id)` → order by fecha DESC
- CRUD estándar SQLAlchemy

## Router (`routers/recursos.py`)

- GET `/` con query params opcionales → service.filtrados
- GET `/{id}` → service.get_by_id
- POST `/` → `current_user.id` → service.create
- PUT/DELETE `/{id}` → valida `existente.usuario_id == current_user.id` → 403 si no → service.update/delete
- GET `/usuario/{id}` / `/materia/{id}` → service.paginado

## Validaciones y Reglas

| Regla | Implementación |
|-------|----------------|
| `titulo` max 150 | `String(150)` BD + Pydantic |
| `url` formato válido | `HttpUrl` en Pydantic |
| `tipo` opcional | `String, nullable=True` |
| Ownership | `usuario_id` del token en create; check `existente.usuario_id == current_user.id` en update/delete → 403 |
| FK materia existe | BD constraint + repo |

## Errores

| Código | Endpoint | Causa |
|--------|----------|-------|
| 403 | PUT/DELETE | Usuario no es dueño |
| 404 | GET/PUT/DELETE by ID | Recurso no existe |
| 422 | POST/PUT | Validación (url inválida, titulo >150, FK) |
| 401 | POST/PUT/DELETE | No autenticado |