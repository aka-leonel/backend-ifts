# Auth - Backend

## Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/auth/registro` | Crea usuario (email único, nombre, apellido, password, carrera_id, rol=estudiante) | ❌ |
| POST | `/auth/login` | Devuelve JWT 24h (HS256) + usuario | ❌ |
| GET | `/auth/me` | Perfil usuario autenticado | ✅ JWT |
| PATCH | `/auth/me` | Actualiza **solo** nombre/apellido (ignora email, carrera) | ✅ JWT |
| GET | `/auth/verify` | Valida token → `{valid, user_id}` | ✅ JWT |
| POST | `/auth/forgot-password` | Envía email reset (mensaje genérico, no revela si email existe) | ❌ |
| POST | `/auth/reset-password` | Consume token URL (30 min, un uso) + nueva password | ❌ |
| PATCH | `/auth/password` | Cambia password **requiere password actual** (re-autenticación) | ✅ JWT |

## Modelos

```python
# Usuario
id, nombre, apellido, email(único), password_hash(bcrypt), carrera_id(FK), rol(estudiante/admin), fecha_registro

# PasswordResetToken
usuario_id(FK), token_hash(SHA256), expira(30min), usado(bool)
```

## Lógica Clave (service.py)

**JWT:** `sub=user_id`, `email`, `exp=24h`, HS256, `SECRET_KEY` de `.env`.

**Registro:** Verifica email único → hash bcrypt → crea usuario → response sin password.

**Login:** Verifica email + bcrypt → genera JWT → retorna token + usuario.

**Reset Password:**
1. `forgot_password`: Si email existe → genera token `secrets.token_urlsafe(32)` → hash SHA256 → guarda con expiración 30min → email SMTP con link `FRONTEND_RESET_PASSWORD_URL?token=...`
2. `reset_password`: Valida token (hash, no expirado, no usado) → hash nueva password → actualiza usuario → marca token usado.

**Cambio Password:** Verifica `password_actual` con bcrypt → 401 si falla → 400 si nueva = actual → hash y actualiza.

## Excepciones

| Código | Cuándo |
|--------|--------|
| 409 | Email duplicado en registro |
| 401 | Credenciales inválidas, token inválido/expirado, password actual incorrecta |
| 400 | Token reset inválido/expirado, password nueva = actual |
| 422 | Validación Pydantic falla |

## Dependencias Auth (`dependencies.py`)

- `get_current_user`: Extrae JWT del header `Authorization: Bearer` → valida → retorna `UsuarioResponse`
- `require_admin`: Verifica `rol == admin` → 403 si no
- `solo_propio_o_admin`: Verifica `user_id == current_user.id` o admin → 403 si no