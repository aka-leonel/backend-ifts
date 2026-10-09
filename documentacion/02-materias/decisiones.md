# Materias - Decisiones Clave

| ID | Decisión | Rationale |
|----|----------|-----------|
| **D010** | Endpoint dedicado `GET /materias/buscar` (no mezclar con listado por carrera) | Búsqueda es patrón de acceso distinto; endpoint separado más claro y semántico; reutiliza `MateriaResponse` y paginación genérica |
| **D009** | Campo `tipo` en **Recurso** (no en Materia) para filtro RF-16 | Campo explícito permite filtrado preciso; consistente con patrón otros campos |
| **D004** | Wrapper único `apiClient` (fetch + interceptors) | Control total, cero deps, tipado TS nativo, consistente en toda la app |
| **D008** | Paginación genérica `PaginatedResponse<T>` + `Paginador` | Backend usa misma estructura para todo; frontend espejo reduce código y bugs |
| **D012** | Formularios declarativos: `FormModal` + `EntityForm` + `*Spec.ts` | Cero deps extra, especificación declarativa, reutilizable, mapeo automático 422→fieldErrors |
| **D013** | `ListState` unificado (loading/error/empty + retry) | Consistencia visual, reducción código, UX uniforme en todas las listas |
| **D018** | `ByteWidget` componente progreso circular compartido | SVG nativo, cero deps, control total animaciones/colores, reutilizable en múltiples tamaños/contextos |
| **D006** | `AuthContext` fuente única + rehidratación `GET /auth/me` en mount | React Context nativo, sin deps, rehidratación valida token con backend, timers evitan 401 sorpresivos |
| **D007** | Navegación `switch(screen)` en memoria (sin React Router) | Cero deps, control total, simple para <20 pantallas, navegación condicional trivial |

## Referencias

| Decisión | Backend | Frontend |
|----------|---------|----------|
| D010 | `app/features/materias/router.py`, `service.py`, `repository.py` | `features/catalogo/service.ts`, `hooks.ts`, `BuscarMateriasScreen` |
| D004 | — | `src/api/client.ts`, todos los `service.ts` |
| D008 | — | `src/shared/schemas/pagination.ts`, `components/Paginador.tsx`, `hooks/useAsyncQuery.ts` |
| D012 | — | `components/FormModal.tsx`, `EntityForm.tsx`, `features/*/materiaUsuarioSpec.ts`, `hooks/useApiForm.ts` |
| D013 | — | `components/ListState.tsx`, `features/materias/MisMateriasScreen.tsx` |
| D018 | — | `components/ByteWidget.tsx`, `features/materias/MateriaCard.tsx`, `PromedioCard.tsx` |
| D006 | — | `src/auth/AuthContext.tsx`, `src/auth/storage.ts`, `features/auth/guards.tsx` |
| D007 | — | `src/App.tsx`, `components/SidebarNav.tsx`, `BottomNav.tsx` |