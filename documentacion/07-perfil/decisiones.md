# Perfil - Decisiones Clave

| ID | Decisión | Rationale |
|----|----------|-----------|
| **D016** | `PATCH /auth/me` **solo nombre/apellido** (email/carrera read-only) | Email = identidad única (cambio requiere verificación futura); Carrera = dato académico estructural (cambio implica revalidar cursadas); Simplicidad: un endpoint, campos permitidos explícitos |
| **D017** | Endpoint real `PATCH /auth/password` (no `/auth/change-password`) | Backend es fuente de verdad; RESTful: `PATCH /auth/me` modifica perfil, `PATCH /auth/password` modifica password |
| **D015** | `suppressUnauthorizedRedirect` en `PATCH /auth/password` | 401 aquí = "password actual incorrecta", NO sesión expirada; flag evita logout global; `useApiForm` mapea 401 a `fieldErrors.password_actual` |
| **D006** | `AuthContext` sync sin reload (`updateUsuario` → state + localStorage) | UX seamless: cambios instantáneos; localStorage persistido cross-session; evita parpadeo/latencia de reload |
| **D028** | CSS Variables para tema/accesibilidad (`--font-size`, `--contrast`, `.dark` en `<html>`) | CSS vars nativas, sin runtime overhead; cambio instantáneo sin re-render React; persistente cross-session via localStorage; compatible Tailwind v4 |

## Referencias

| Decisión | Backend | Frontend |
|----------|---------|----------|
| D016 | `app/features/auth/schema.py` (PerfilUpdate), `service.py` | `features/perfil/perfilSpec.ts`, `PerfilScreen.tsx` |
| D017 | `app/features/auth/router.py` (PATCH /auth/password), `service.py` | `src/api/auth.ts`, `features/perfil/hooks.ts` |
| D015 | — | `src/api/client.ts` (suppressUnauthorizedRedirect), `features/perfil/CambiarPasswordModal.tsx` |
| D006 | — | `src/auth/AuthContext.tsx` (updateUsuario), `features/perfil/hooks.ts` |
| D028 | — | `lib/preferencias.ts`, `index.css`, `features/perfil/AccesibilidadPanel.tsx` |