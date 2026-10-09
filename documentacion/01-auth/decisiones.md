# Auth - Decisiones Clave

| ID | Decisión | Rationale |
|----|----------|-----------|
| **D005** | JWT 24h en localStorage + memoria, **sin refresh token** | Simplicidad: 24h cubre sesión diaria típica; localStorage permite rehidratación instantánea; sin refresh reduce superficie de ataque y complejidad backend |
| **D014** | Reset password **sin router**: token en query param (`/reset-password?token=...`), `App.tsx` lo lee en mount | App usa navegación `switch(screen)` en memoria (sin React Router); query param es estándar en emails; un solo componente maneja token presente/ausente |
| **D015** | `suppressUnauthorizedRedirect` en `PATCH /auth/password` | 401 aquí = "password actual incorrecta", NO sesión expirada. Flag evita logout global; `useApiForm` mapea 401 a `fieldErrors.password_actual` |
| **D016** | `PATCH /auth/me` **solo nombre/apellido** (email/carrera read-only) | Email = identidad única (cambio requiere verificación futura); Carrera = dato académico estructural (cambio implica revalidar cursadas). Backend ignora campos no permitidos |
| **D017** | Endpoint real es `PATCH /auth/password` (no `/auth/change-password`) | Backend es fuente de verdad; RESTful: `PATCH /auth/me` modifica perfil, `PATCH /auth/password` modifica password |
| **D001** | `SECRET_KEY` fallback inseguro en código | Permite `uvicorn --reload` out-of-the-box en dev. **Crítico**: cambiar en producción (CI/CD debe validar) |
| **D002** | Bcrypt para hashing (`passlib[bcrypt]`) | Estándar probado, work factor 12, resistente a GPU |
| **D003** | Token reset: SHA256 hash + 30 min expiración + un uso | SHA256 rápido e irreversible; 30 min balance usabilidad/seguridad; campo `usado` previene replay |

## Referencias de Archivos

| Decisión | Backend | Frontend |
|----------|---------|----------|
| D005 | `app/features/auth/service.py` (JWT config) | `src/auth/AuthContext.tsx`, `src/auth/storage.ts` |
| D014 | `app/features/auth/router.py` | `src/App.tsx`, `src/features/auth/ResetPasswordScreen.tsx` |
| D015 | `app/features/auth/router.py` | `src/api/client.ts`, `src/features/perfil/CambiarPasswordModal.tsx` |
| D016 | `app/features/auth/schema.py` (PerfilUpdate), `service.py` | `src/features/perfil/perfilSpec.ts`, `PerfilScreen.tsx` |
| D017 | `app/features/auth/router.py` | `src/api/auth.ts` |
| D001-003 | `app/features/auth/service.py`, `model.py` | — |