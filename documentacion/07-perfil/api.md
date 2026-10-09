# Perfil - Contrato API

## Tipos

```typescript
interface PerfilUpdate { nombre?: string; apellido?: string; }
interface CambiarPasswordRequest { password_actual: string; password_nueva: string; }
interface UsuarioResponse { id, nombre, apellido, email, carrera_id, carrera_nombre?, rol, fecha_registro }
interface MensajeResponse { detail: string }
```

## Endpoints

### GET `/auth/me` (Auth: JWT)
Response 200: `UsuarioResponse`  
Errores: 401

### PATCH `/auth/me` (Auth: JWT)
Body: `PerfilUpdate` (partial, solo nombre/apellido)  
Response 200: `UsuarioResponse` actualizado  
**Campos permitidos:** Solo `nombre`, `apellido`  
**Ignorados:** `email`, `carrera_id` (read-only)  
Errores: 401, 422

### PATCH `/auth/password` (Auth: JWT)
Body: `CambiarPasswordRequest`  
Response 200: `MensajeResponse`  
**Frontend:** `suppressUnauthorizedRedirect: true` en `apiClient`  
Validaciones backend:
1. `password_actual` coincide → 401 si no
2. `password_nueva` ≠ `password_actual` → 400 si iguales
3. Hash y actualiza  
Errores: 401 (token O password actual), 400 (nueva = actual), 422

## Ejemplos

### Actualizar Perfil
```bash
PATCH /auth/me
Authorization: Bearer <token>
{ "nombre": "Juan Carlos", "apellido": "Pérez González" }
```

### Cambiar Password
```bash
PATCH /auth/password
Authorization: Bearer <token>
{ "password_actual": "password123", "password_nueva": "nuevaPassword456" }
```

## Frontend Service

```typescript
authApi.me()                           // GET /auth/me
authApi.updateMe(data)                 // PATCH /auth/me
authApi.changePassword(data)           // PATCH /auth/password (suppressUnauthorizedRedirect: true)
```

## Códigos Error

| Endpoint | 400 | 401 | 422 |
|----------|-----|-----|-----|
| GET /auth/me | | ✓ | |
| PATCH /auth/me | | ✓ | ✓ |
| PATCH /auth/password | ✓ | ✓ | ✓ |