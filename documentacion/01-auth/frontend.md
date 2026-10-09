# Auth - Frontend

## Pantallas

| Pantalla | Ruta | Descripción |
|----------|------|-------------|
| Login | `/login` | Email + password, link "¿Olvidé contraseña?", botón registrar |
| Registro | `/registro` | 2 pasos: (1) datos + password, (2) select carrera |
| Olvidé Password | `/olvide-password` | Solo email → siempre mensaje éxito |
| Reset Password | `/reset-password?token=...` | Lee token de query param → nueva password + confirmación |

## Arquitectura

### `AuthContext` (Fuente única)
- State: `usuario`, `token`, `isAuthenticated`, `isLoading`
- Mount: si hay token en localStorage → `GET /auth/me` (rehidratación)
- Timers: warning 60s antes expiración + logout auto
- Métodos: `login(token, usuario)`, `logout()`, `updateUsuario(data)`, `refreshUsuario()`
- Persistencia: memoria + localStorage sincronizados

### `apiClient` (Wrapper HTTP único)
- Base URL: `VITE_API_URL`
- Interceptor request: inyecta `Authorization: Bearer <token>`
- Interceptor response: parsea `ApiError{detail, errors[]}`, 401→logout (salvo `suppressUnauthorizedRedirect`), 204 no parsea
- Tipado genérico: `fetch<T>(url, options)`

### Guards
- `RutaProtegida`: Requiere auth → sino redirect `/login`
- `RutaAdmin`: Requiere `rol === "admin"` → sino redirect `/`

## Flujos

**Login/Registro:** `useApiForm` → `authApi.login/register` → `AuthContext.login()` → timers + localStorage → redirect `/` (estudiante) o `/admin` (admin).

**Olvidé Password:** `POST /forgot-password` → siempre 200 + toast genérico.

**Reset Password:** `App.tsx` lee `token` de `window.location.search` → `ResetPasswordScreen` → `POST /reset-password` → 400 token inválido → redirect `/olvide-password`.

**Cambio Password (Perfil):** `PATCH /auth/password` con `suppressUnauthorizedRedirect=true` → 401 = "password actual incorrecta" → `fieldErrors.password_actual` (NO logout).

## Validaciones Cliente

| Campo | Regla |
|-------|-------|
| email | Formato válido, required |
| password | Min 8 chars, required |
| confirmPassword | === password (registro/cambio) |
| nombre/apellido | Required, max 50 |

## Storage Helpers (`storage.ts`)
`saveAuth(token, usuario, expiresIn)`, `getAuth()`, `clearAuth()` → localStorage keys: `miifts_token`, `miifts_usuario`, `miifts_token_expiry`.