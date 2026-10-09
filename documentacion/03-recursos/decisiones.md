# Recursos - Decisiones Clave

| ID | Decisión | Rationale |
|----|----------|-----------|
| **D009** | Campo `tipo` explícito en `Recurso` (no derivar de URL) | Filtro preciso (RF-16); simple, mantenible, extensible; URLs pueden no tener extensión |
| **D020** | Feature `recursos` **independiente** de `catalogo` | Lectura pública vs CRUD privado con ownership; diferentes validaciones, permisos, UI; evita condicionales `if (isAdmin)` |
| **D012** | Formularios declarativos: `FormModal` + `EntityForm` + `recursoSpec` | Consistencia UX, reutilización (cursadas, recordatorios), mapeo automático 422→fieldErrors |
| **D013** | `ListState` unificado para loading/error/empty | Estados visuales consistentes en toda la app |
| **D004** | `apiClient` único para HTTP | Auth automático, 401→logout, 422 parseado, 204 no parseado |
| **D008** | Paginación genérica `PaginatedResponse<T>` + `Paginador` | Misma UX paginación en toda la app |

## Referencias

| Decisión | Backend | Frontend |
|----------|---------|----------|
| D009 | `app/features/recursos/model.py`, `schema.py`, `repository.py`, `service.py` | `features/recursos/recursoSpec.ts`, `service.ts`, `hooks.ts` |
| D020 | — | `features/recursos/` (independiente de `features/catalogo/`) |
| D012 | — | `components/FormModal.tsx`, `EntityForm.tsx`, `features/recursos/recursoSpec.ts`, `hooks/useApiForm.ts` |
| D013 | — | `components/ListState.tsx`, `features/recursos/RecursosScreen.tsx` |
| D004 | — | `src/api/client.ts`, `features/recursos/service.ts` |
| D008 | — | `src/shared/schemas/pagination.ts`, `components/Paginador.tsx`, `hooks/useAsyncQuery.ts` |