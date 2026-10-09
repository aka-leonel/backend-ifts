# Perfil - Backend

## Endpoints (módulo Auth)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/auth/me` | Perfil usuario autenticado |
| PATCH | `/auth/me` | Actualiza **solo** `nombre`/`apellido` (ignora email, carrera) |
| PATCH | `/auth/password` | Cambia password **requiere `password_actual`** (re-autenticación) |

## Service (`AuthService`)

### `actualizar_perfil(user_id, datos: PerfilUpdate)`
- `datos.model_dump(exclude_unset=True)` → solo campos enviados
- `repository.update(user_id, **cambios)` → retorna `UsuarioResponse`
- **No permite** cambiar email ni carrera (no están en `PerfilUpdate`)

### `cambiar_password(user_id, password_actual, password_nueva)`
1. Verifica usuario existe
2. `verify_password(password_actual, user.password_hash)` → 401 si falla
3. `password_actual == password_nueva` → 400
4. Hash nueva password → `repository.update(user_id, password_hash=hashed)`

## Router

```python
GET /me → current_user (via get_current_user dependency)
PATCH /me → service.actualizar_perfil(current_user.id, cambios)
PATCH /password → service.cambiar_password(current_user.id, password_actual, password_nueva)
```

## Schemas

```python
PerfilUpdate: nombre?, apellido?
CambiarPasswordRequest: password_actual, password_nueva
UsuarioResponse: id, nombre, apellido, email, carrera_id, carrera_nombre?, rol, fecha_registro
MensajeResponse: detail
```

## Reglas

| Regla | Implementación |
|-------|----------------|
| Email read-only | No en `PerfilUpdate`; backend ignora si llega |
| Carrera read-only | No en `PerfilUpdate`; cambio requiere revalidar cursadas (futuro) |
| Cambio password requiere actual | `verify_password` → 401 "La contraseña actual es incorrecta" |
| Password nueva ≠ actual | Check explícito → 400 |
| 401 en cambio password NO hace logout | Frontend usa `suppressUnauthorizedRedirect=true` |

## Errores

| Código | Endpoint | Causa |
|--------|----------|-------|
| 401 | GET/PATCH /me, PATCH /password | Token inválido/expirado |
| 401 | PATCH /password | Password actual incorrecta |
| 400 | PATCH /password | Password nueva = actual |
| 422 | PATCH /me, PATCH /password | Validación |