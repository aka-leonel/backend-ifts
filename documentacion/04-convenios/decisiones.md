# Convenios + TalentoTech — Decisiones clave

> Última actualización: 2026-11-04.
> Los IDs `D15…D20` provienen de `context/decisions.md` (backend).
> Los IDs `D004…D020` son los del frontend (`frontend-miifts/docs/context/decisions.md`).

---

## 1. Decisiones de contrato (backend)

| ID | Decisión | Rationale |
|---|---|---|
| **D15** | `?q=` en convenios: `ILIKE %texto%` en `institucion`, `carrera_destino` y `descripcion` | Búsqueda simple y suficiente para el catálogo; case-insensitive sin depender de extensiones (full-text/`unaccent`). `q` vacío no filtra. |
| **D16** | `PATCH /convenios/{id}` parcial; `PUT` sigue siendo reemplazo total | El admin edita campos sueltos sin reenviar todo; `PUT` queda para reemplazos explícitos. Body `{}` ⇒ 200 sin cambios. |
| **D17** | Convenios: N:M `convenios_carreras` + flag `todas_las_carreras` (flag e ids excluyentes) | Un convenio puede aplicar a varias carreras de origen o a todas sin duplicar filas. Wildcard ⇒ `carreras: []` y sin filas en la intermedia. La unicidad pasa a `(institucion, carrera_destino)`. |
| **D19** | Orden `lower(institucion) ASC, id ASC` en convenios | Alfabético case-insensitive y determinista (desempate por `id`), necesario para paginar sin duplicados/huecos. |
| **D20** | TalentoTech replica D17 + response de card + unicidad `(institucion, nombre_curso)` + orden `lower(nombre_curso)` y **sin `PATCH`** | Misma semántica que convenios para carreras; la card necesita institución, modalidad, dificultad y carreras. `dificultad` nullable porque la data puede no traerla. La edición es `PUT` completo para no duplicar la lógica de parcial. |

### Consecuencias relevantes

- `carrera_id` desaparece de convenios (D17) y de TalentoTech (D20): breaking
  change en request y response.
- `todas_las_carreras = true` **no** crea filas en la tabla intermedia; aparece
  en `GET .../carrera/{id}` de cualquier carrera existente.
- Si la carrera no existe, el listado por carrera devuelve **vacío `200`**
  (no `404`), incluso con wildcard.
- La comparación de unicidad es **case-sensitive** y no pliega acentos.
- Borrar una carrera con asociaciones explícitas puede fallar por FK en
  PostgreSQL ⇒ `409 Conflictos de integridad de datos` genérico. SQLite local no
  fuerza FKs por defecto.

---

## 2. Decisiones de frontend

| ID | Decisión | Rationale |
|---|---|---|
| **D020** | Feature `convenios-admin` **separada** de `convenios` (lectura) | Lectura pública sin auth + tabs + cards vs CRUD admin con formularios/validaciones; evita condicionales `if (isAdmin)` dispersos. |
| **D012** | Formularios admin: `FormModal` + `EntityForm` + `convenioSpec` / `talentoTechSpec` | Consistencia con recursos/recordatorios/cursadas; reutilización de componentes y mapeo automático de `422`. |
| **D008** | Paginación genérica en listas públicas y admin | `PaginatedResponse<T>` + `Paginador` + `useAsyncQuery` ⇒ misma UX. |
| **D013** | `ListState` unificado | Loading/error/empty consistentes. |
| **D004** | `apiClient` único | Auth automático, 401→logout, 422 parseado, 204 sin body. |
| **Admin TalentoTech separado** | `features/talentotech-admin/` (no dentro de `convenios-admin`) | El ABM de cursos trabaja con la forma cruda del backend (`TalentoTech`), mientras la sección del estudiante mapea otra forma UI. Separar evita mezclar responsabilidades. |
| **Carreras: multi-select + switch** | `carrera_ids` (multiselect) y `todas_las_carreras` (switch) excluyentes en ambos specs | Refleja la invariante del backend; el submit valida “al menos una” o “todas” antes de enviar. |
| **Categoría TalentoTech: texto libre + select dinámico** | Backend `String(20)` sin enum. El admin la edita como texto; el filtro del estudiante se puebla con las categorías observadas en un catálogo acotado (`per_page=100`) + la activa | No hay endpoint de categorías; hardcodear opciones se desalinea con la data real. Limitación: con más de 100 cursos el catálogo puede quedar incompleto. |
| **Convenios admin usa `PATCH`; TalentoTech admin usa `PUT`** | `editarConvenio` → `PATCH`; `editarTalentoTech` → `PUT` completo | Convenios expone `PATCH`; TalentoTech no. El formulario de TalentoTech envía el body completo. |
| **Validación de URL en el cliente** | `type: "url"` en `FieldSpec` + validación `http/https` en `aBody` | Feedback inmediato antes del submit; evita round-trips `422`. |

---

## 3. Referencias

| Decisión | Backend | Frontend |
|---|---|---|
| D15 / D16 / D17 / D19 | `app/features/recursos/{repository,service,routers/convenios}.py` | `features/convenios/`, `features/convenios-admin/` |
| D20 | `app/features/recursos/{model,schema,repository,service,routers/talentotech}.py` | `features/talentotech/`, `features/talentotech-admin/` |
| D020 | — | `features/convenios/` vs `features/convenios-admin/` |
| D012 | — | `convenioSpec.ts`, `talentoTechSpec.ts`, `FormModal`, `EntityForm`, `useApiForm` |
| D008 | — | `src/api/types.ts` (`Paginated<T>`), `components/Paginador.tsx`, `hooks/useAsyncQuery.ts` |
| D013 | — | `components/ListState.tsx` |
| D004 | — | `src/api/client.ts`, `features/*/service.ts` |
