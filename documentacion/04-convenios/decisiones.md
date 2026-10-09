# Convenios - Decisiones Clave

| ID | Decisión | Rationale |
|----|----------|-----------|
| **D020** | Feature `convenios-admin` **separada** de `convenios` (lectura) | Lectura pública sin auth + tabs + cards vs CRUD admin con formularios/validaciones; evita condicionales `if (isAdmin)` dispersos; responsabilidades claras |
| **D012** | Formularios admin: `FormModal` + `EntityForm` + `convenioAdminSpec` | Consistencia con recursos/recordatorios/cursadas; reutilización componentes; mapeo automático 422 |
| **D008** | Paginación genérica en listas públicas y admin | `PaginatedResponse<T>` + `Paginador` + `useAsyncQuery` → misma UX |
| **D013** | `ListState` unificado | Loading/error/empty consistentes |
| **D004** | `apiClient` único | Auth automático, 401→logout, 422 parseado, 204 no parseado |
| **Validación URL cliente** | `type: "url"` en `FieldSpec` + pattern regex | Feedback inmediato antes de submit, reduce round-trips 422 |
| **Categoría TalentoTech: valores libres + sugeridos** | Backend `String(20)` sin enum; frontend select con opciones (Programación, Data, UX, Diseño, Marketing, Otro) + `allowCustom: true` | Backend flexible para nuevas categorías; frontend guía UX pero permite extensibilidad |

## Referencias

| Decisión | Backend | Frontend |
|----------|---------|----------|
| D020 | — | `features/convenios/` vs `features/convenios-admin/` |
| D012 | — | `features/convenios-admin/convenioAdminSpec.ts`, `FormModal`, `EntityForm`, `useApiForm` |
| D008 | — | `src/shared/schemas/pagination.ts`, `components/Paginador.tsx`, `hooks/useAsyncQuery.ts` |
| D013 | — | `components/ListState.tsx` |
| D004 | — | `src/api/client.ts`, `features/convenios/service.ts`, `features/convenios-admin/service.ts` |