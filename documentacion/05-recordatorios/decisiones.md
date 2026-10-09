# Recordatorios - Decisiones Clave

| ID | Decisión | Rationale |
|----|----------|-----------|
| **D011** | Extender `GET /recordatorios/` con query params (no crear `/buscar` separado) | Búsqueda es variante del listado por usuario con filtros adicionales; evita duplicación de ruta; convención `/recordatorios?tipo=examen&...` |
| **D012** | Formularios declarativos: `FormModal` + `EntityForm` + `recordatorioSpec` | Consistencia con recursos/cursadas; reutilización; mapeo automático 422→fieldErrors |
| **D013** | `ListState` + Agrupación visual "Esta semana" / "Más adelante" (cliente) | Agrupación es concern de presentación; backend sigue paginación estándar; cliente reagrupa si cambia criterio |
| **D008** | Paginación genérica | `PaginatedResponse<T>` + `Paginador` + `useAsyncQuery` → misma UX en toda la app |
| **D004** | `apiClient` único | Auth automático, 401→logout, 422 parseado, 204 no parseado |
| **Tipo: String libre vs Enum** | Backend `String` sin constraint; frontend select 4 opciones | Backend flexible para futuros tipos; frontend guía UX |
| **materia_id opcional** | Nullable en BD; frontend filtra opciones a materias cursadas | Recordatorio puede ser genérico; si se asocia, frontend sugiere relevantes |

## Referencias

| Decisión | Backend | Frontend |
|----------|---------|----------|
| D011 | `app/features/recordatorios/router.py`, `service.py`, `repository.py` | `features/recordatorios/hooks.ts`, `service.ts` |
| D012 | — | `features/recordatorios/recordatorioSpec.ts`, `FormModal`, `EntityForm`, `useApiForm` |
| D013 | — | `features/recordatorios/RecordatoriosScreen.tsx`, `components/ListState.tsx` |
| D008 | — | `src/shared/schemas/pagination.ts`, `components/Paginador.tsx`, `hooks/useAsyncQuery.ts` |
| D004 | — | `src/api/client.ts`, `features/recordatorios/service.ts` |