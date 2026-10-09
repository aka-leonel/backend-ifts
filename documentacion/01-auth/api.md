# Auth - Contrato API

## Tipos (generados openapi-typescript)

```typescript
// Request
interface UsuarioCreate { nombre, apellido, email, password, carrera_id, rol?: "estudiante"|"admin" }
interface UsuarioLogin { email, password }
interface PerfilUpdate { nombre?, apellido? }
interface ForgotPasswordRequest { email }
interface ResetPasswordRequest { token, password }
interface CambiarPasswordRequest { password_actual, password_nueva }

// Response
interface UsuarioResponse { id, nombre, apellido, email, carrera_id, carrera_nombre?, rol, fecha_registro }
interface TokenResponse { access_token, token_type: "bearer", usuario: UsuarioResponse }
interface VerifyResponse { valid: boolean, user_id: number }
interface MensajeResponse { detail: string }

// Error unificado
interface ApiError { detail: string, errors?: { campo: string, msg: string }[] }
```

## Endpoints

### POST `/auth/registro` → 201 `UsuarioResponse`
Body: `UsuarioCreate`  
Errores: 409 email duplicado, 422 validación

### POST `/auth/login` → 200 `TokenResponse`
Body: `UsuarioLogin`  
Errores: 401 credenciales inválidas + header `WWW-Authenticate: Bearer`

### GET `/auth/me` → 200 `UsuarioResponse`
Header: `Authorization: Bearer <token>`  
Errores: 401

### PATCH `/auth/me` → 200 `UsuarioResponse`
Header: `Authorization: Bearer <token>`  
Body: `PerfilUpdate` (solo nombre/apellido; email/carrera ignorados)  
Errores: 401, 422

### GET `/auth/verify` → 200 `VerifyResponse`
Header: `Authorization: Bearer <token>`  
Errores: 401

### POST `/auth/forgot-password` → 200 `MensajeResponse`
Body: `ForgotPasswordRequest`  
**Siempre 200** (no revela si email existe)

### POST `/auth/reset-password` → 200 `MensajeResponse`
Body: `ResetPasswordRequest`  
Errores: 400 token inválido/expirado/usado, 422

### PATCH `/auth/password` → 200 `MensajeResponse`
Header: `Authorization: Bearer <token>`  
Body: `CambiarPasswordRequest`  
**Frontend:** `suppressUnauthorizedRedirect: true`  
Errores: 401 password actual incorrecta, 400 nueva = actual, 422

## JWT Payload
```json
{ "sub": "1", "email": "user@test.com", "exp": 1705312200, "iat": 1705225800 }
```
- Algoritmo: HS256
- Expiración: 24h
- Header: `Authorization: Bearer <token>`

## Códigos de Error por Endpoint

| Endpoint | 400 | 401 | 409 | 422 |
|----------|-----|-----|-----|-----|
| registro | | ✓ | ✓ | ✓ |
| login | | ✓ | | ✓ |
| me | | ✓ | | ✓ |
| me (PATCH) | | ✓ | | ✓ |
| verify | | ✓ | | |
| forgot-password | | | | ✓ |
| reset-password | ✓ | | | ✓ |
| password (PATCH) | ✓ | ✓ | | ✓ |