# Admin - Decisiones Clave

| ID | Decisión | Rationale |
|----|----------|-----------|
| **D019** | Nav admin **reemplaza** (no suma) al de estudiante | Separación contextos: admin=gestión, estudiante=consumo; reduce ruido cognitivo y superficie de ataque; consistencia: rol define vista completa |
| **D020** | Feature `convenios-admin` separada de `convenios` (lectura) | Lectura pública sin auth + tabs + cards vs CRUD admin con formularios/validaciones; evita condicionales `if (isAdmin)` |
| **D012** | Formularios admin: `FormModal` + `EntityForm` + `*AdminSpec` | Consistencia con recursos/recordatorios/cursadas; reutilización componentes; mapeo automático 422/409 |
| **D008** | Paginación genérica en listas admin | `PaginatedResponse<T>` + `Paginador` + `useAsyncQuery` → misma UX que features públicas |
| **D013** | `ListState` unificado en admin | Loading/error/empty consistentes |
| **D004** | `apiClient` único para admin | Auth automático, 401→logout, 422 parseado, 204 no parseado |
| **D029** | Tipos generados `openapi-typescript` para admin | Single source of truth: backend OpenAPI; regeneración automática (`npm run gen:api`); TS compile-time validation |
| **D030** | Sub-tabs en Catálogo Admin (Carreras / Materias / Correlativas) | Contexto compartido (catálogo académico); navegación rápida sin recargar shell; estado persistido en sessionStorage (opcional) |
| **D031** | Correlativas Admin: 2 selects + validación ciclo cliente | Feedback inmediato evita request fallido; backend autoridad final (ciclos indirectos solo detectables en BD) |

## Referencias

| Decisión | Backend | Frontend |
|----------|---------|----------|
| D019 | — | `components/SidebarNav.tsx`, `BottomNav.tsx`, `src/App.tsx`, `src/auth/AuthContext.tsx` |
| D020 | — | `features/convenios/` vs `features/convenios-admin/` |
| D012 | — | `features/catalogo-admin/*AdminSpec.ts`, `features/convenios-admin/convenioAdminSpec.ts`, `FormModal`, `EntityForm` |
| D008 | — | `src/shared/schemas/pagination.ts`, `components/Paginador.tsx`, `hooks/useAsyncQuery.ts` |
| D013 | — | `components/ListState.tsx` |
| D004 | — | `src/api/client.ts`, `features/catalogo-admin/service.ts`, `features/convenios-admin/service.ts` |
| D029 | — | `npm run gen:api`, `src/api/schema.d.ts`, `features/catalogo-admin/service.ts` |
| D030 | — | `features/admin/AdminScreen.tsx`, `features/catalogo-admin/CatalogoAdminScreen.tsx` |
| D031 | `app/features/materias/service.py` (DFS ciclo) | `features/catalogo-admin/correlativaAdminSpec.ts`, `CorrelativasAdmin.tsx` |