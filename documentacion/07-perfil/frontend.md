# Perfil - Frontend

## Pantalla `/perfil`

### Estructura
- **Header:** Avatar + nombre + email + badge carrera + badge rol
- **Formulario nombre/apellido:** `EntityForm` + `perfilSpec` → `PATCH /auth/me`
- **Sync sin reload:** `onSuccess` → `AuthContext.updateUsuario(updated)` (state + localStorage)
- **Progreso carrera:** Widget usando `usePromedio` + `useMisMaterias`
- **Accesibilidad:** `AccesibilidadPanel` (tema, font-size, alto contraste)
- **Cambiar password:** Modal `FormModal` + `cambiarPasswordSpec` → `PATCH /auth/password` con `suppressUnauthorizedRedirect`
- **Logout:** Button destructivo → `AuthContext.logout()` + redirect `/login`

---

## Hooks (`features/perfil/hooks.ts`)

```typescript
useAuthMe() → { usuario, loading, error, refetch }  // GET /auth/me + sync con AuthContext
useActualizarPerfil() → useApiForm<PerfilUpdate, UsuarioResponse>  // PATCH /auth/me
useCambiarPassword() → useApiForm<CambiarPasswordRequest, MensajeResponse>  // PATCH /auth/password con suppressUnauthorizedRedirect
```

## Specs

```typescript
perfilSpec = [
  { name: "nombre", label: "Nombre", type: "text", required: true, maxLength: 50 },
  { name: "apellido", label: "Apellido", type: "text", required: true, maxLength: 50 }
  // email y carrera NO están (read-only)
]

cambiarPasswordSpec = [
  { name: "password_actual", label: "Contraseña actual", type: "password", required: true },
  { name: "password_nueva", label: "Nueva contraseña", type: "password", required: true, minLength: 8 },
  { name: "confirmPassword", label: "Confirmar nueva", type: "password", required: true }
]
// Validación cliente: password_nueva === confirmPassword
```

## Accesibilidad (`AccesibilidadPanel.tsx` + `preferencias.ts`)

- **Tema:** Select (claro / oscuro / sistema) → CSS class `.dark` en `<html>`
- **Tamaño fuente:** Select (sm / base / lg) → CSS var `--font-size`
- **Alto contraste:** Switch → CSS var `--contrast` (normal/high)

### `preferencias.ts`
- Guarda en localStorage + aplica vars al `<html>` element
- `applyPreferencias(prefs)` → `root.style.setProperty("--font-size", ...)`, `root.classList.toggle("dark", ...)`

### `index.css` (Tailwind v4)
```css
:root {
  --c-bg: #ffffff; --c-card: #f8fafc; --c-primary: #2563eb;
  --c-text: #1e293b; --c-border: #e2e8f0;
  --font-size: 1rem; --contrast: normal;
}
.dark { --c-bg: #0f172a; --c-card: #1e293b; --c-primary: #3b82f6; --c-text: #f1f5f9; }
@media (prefers-contrast: high) { :root { --contrast: high; } }
```
> Componentes usan `bg-[var(--c-card)]` etc. en lugar de clases hardcoded.

## Validaciones Cliente

| Campo | Regla |
|-------|-------|
| `nombre`/`apellido` | Required, max 50 |
| `password_actual` | Required |
| `password_nueva` | Required, min 8, ≠ `password_actual` |
| `confirmPassword` | Required, === `password_nueva` |

## Errores

| Backend | Frontend |
|---------|----------|
| 401 me/updateMe | `apiClient` → logout + redirect login |
| 401 changePassword | `suppressUnauthorizedRedirect` → `fieldErrors.password_actual` = "Contraseña actual incorrecta" |
| 400 password nueva = actual | Toast error |
| 422 validación | `fieldErrors` por campo |

## Sync Sin Reload

```typescript
useActualizarPerfil.onSuccess = (updated) => {
  updateUsuario(updated);  // AuthContext: state + localStorage simultáneo
  // NO reload, NO navigate → UX seamless
}
```