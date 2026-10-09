# Recordatorios - Backend

## Endpoints (auth: usuario logueado, own only)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/recordatorios/` | Lista paginada + filtros (`tipo`, `desde`, `hasta`, `materia_id`), orden `fecha DESC` |
| POST | `/recordatorios/` | Crea (usuario_id del token) |
| PATCH | `/recordatorios/{id}` | Actualiza parcial |
| DELETE | `/recordatorios/{id}` | Elimina |

## Modelo

```python
Recordatorio: id, titulo, fecha(DateTime), tipo, usuario_id(FK), materia_id(FK nullable)
```

## Service

- `get_recordatorios_filtrados_paginado(usuario_id, tipo, desde, hasta, materia_id, params)` → repo.query_search + paginate
- `create_recordatorio(db, recordatorio, usuario_id)` → repo.create
- `update_recordatorio(db, id, datos, usuario_id)` → repo.update (WHERE id=? AND usuario_id=?) → 404 si no encontrado
- `delete_recordatorio(db, id, usuario_id)` → repo.delete (WHERE id=? AND usuario_id=?) → 404 si no encontrado

## Repository

- `query_search(usuario_id, tipo, desde, hasta, materia_id)` → filtros opcionales + `order_by(fecha.desc())`
- `create(recordatorio)` / `update(id, usuario_id, cambios)` / `delete(id, usuario_id)` → ownership en WHERE

## Router

```python
@router.get("/") → service.filtrados(current_user.id, query_params)
@router.post("/") → service.create(recordatorio, current_user.id)
@router.patch("/{id}") → service.update(id, cambios, current_user.id)
@router.delete("/{id}") → service.delete(id, current_user.id)
```

## Filtros Query

| Param | Tipo | Descripción |
|-------|------|-------------|
| `tipo` | string | Exacto ("parcial", "tp", "final", "otro") |
| `desde` | date | Fecha >= (YYYY-MM-DD) |
| `hasta` | date | Fecha <= (YYYY-MM-DD) |
| `materia_id` | int | Filtra por materia |
| `page`, `per_page` | int | Paginación estándar |

## Tipos de Recordatorio

Valores esperados: `parcial`, `tp`, `final`, `otro` (String libre en BD, frontend usa select 4 opciones).

## Reglas

- Usuario solo ve sus recordatorios (`usuario_id = current_user.id` en todos queries)
- Usuario solo modifica/elimina los suyos (WHERE id=? AND usuario_id=?)
- `materia_id` opcional (nullable en BD)
- Orden por fecha descendente (más próximos primero)
- Filtros opcionales combinables (query dinámico)

## Errores

| Código | Endpoint | Causa |
|--------|----------|-------|
| 401 | Todos | No autenticado |
| 404 | PATCH, DELETE | Recordatorio no existe o no es del usuario |
| 422 | POST, PATCH | Validación (fecha inválida, tipo vacío, FK) |