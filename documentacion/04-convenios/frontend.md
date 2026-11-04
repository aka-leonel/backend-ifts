# Convenios + TalentoTech — Frontend

> Última actualización: 2026-11-04.
> Repo: `frontend-miifts`. Contrato backend: `docs/CONVENIOS_FRONT.md`,
> `docs/TALENTOTECH_FRONT.md`.

---

## 1. Features

| Feature | Carpeta | Rol |
|---|---|---|
| Convenios (lectura) | `src/features/convenios/` | Estudiante, público |
| Convenios admin | `src/features/convenios-admin/` | Admin (CRUD) |
| TalentoTech (lectura) | `src/features/talentotech/` | Estudiante, público |
| TalentoTech admin | `src/features/talentotech-admin/` | Admin (CRUD) |

### Integración en pantallas

- **Estudiante:** `features/convenios/ConveniosScreen.tsx` tiene tabs
  **“Universidades”** y **“Talento Tech”**. La segunda renderiza
  `features/talentotech/TalentoTechSection`.
- **Admin:** `features/admin/AdminScreen.tsx` tiene tabs **“Catálogo”**,
  **“Convenios”** y **“Talento Tech”** (esta última monta
  `TalentoTechAdminScreen`).

---

## 2. Tipos

`src/api/types.ts` reexporta los tipos generados:

```typescript
export type CarreraResumen = S["CarreraResumen"];
export type Convenio        = S["ConvenioResponse"];
export type ConvenioCreate  = S["ConvenioCreate"];
export type ConvenioUpdate  = S["ConvenioUpdate"];
export type TalentoTech     = S["TalentoTechResponse"];
export type TalentoTechCreate = S["TalentoTechCreate"];
// No hay TalentoTechUpdate: el PUT usa TalentoTechCreate.
```

`S` sale de `src/api/schema.d.ts`, generado desde `docs/openapi.json` con:

```bash
npm run gen:api
```

> Si el backend cambia el contrato, regenerá este archivo antes de tocar tipos a
> mano.

---

## 3. Servicios

| Función | Endpoint | Notas |
|---|---|---|
| `getConvenios({ page, per_page, q, carrera_id })` | `GET /convenios/` o `/convenios/carrera/{id}` | `carrera_id` cambia el path; `q` va en query |
| `getConveniosAdmin({ page, per_page, q })` | `GET /convenios/` | Admin |
| `crearConvenio(body)` | `POST /convenios/` | Admin |
| `editarConvenio(id, body)` | `PATCH /convenios/{id}` | Admin (parcial) |
| `borrarConvenio(id)` | `DELETE /convenios/{id}` | Admin |
| `getTalentoTech({ page, per_page, categoria, carrera_id })` | `GET /talentotech/`, `/carrera/{id}` o `/categoria/{cat}` | Prioridad: categoría > carrera > listado |
| `getTalentoTechAdmin({ page, per_page })` | `GET /talentotech/` | Admin |
| `crearTalentoTech(body)` | `POST /talentotech/` | Admin |
| `editarTalentoTech(id, body)` | `PUT /talentotech/{id}` | Admin (body completo, sin `PATCH`) |
| `borrarTalentoTech(id)` | `DELETE /talentotech/{id}` | Admin |

Hooks: `useConvenios(params)` y `useTalentoTech(params)` sobre `useAsyncQuery`.

---

## 4. Convenios — estudiante

### 4.1 Mapeo a la UI

`getConvenios` mapea `ConvenioResponse` a `ConvenioItem`:

```typescript
type ConvenioItem = {
  id: number;
  nombre: string;              // institucion
  carrera_destino?: string;
  descripcion: string;
  carreras: CarreraResumen[];
  todas_las_carreras: boolean;
  logo: string;                // inicial de la institución
  link_info: string;
};
```

### 4.2 Pantalla

- Buscador con **debounce de 350 ms** → `useConvenios({ page, q })`.
- Placeholder: “Buscar por institución, carrera o descripción.”
- `ListState` + `Paginador` (`total_pages`).
- No hay filtro por carrera en la pantalla; el servicio soporta `carrera_id`
  pero no está cableado a la UI.

### 4.3 Card y modal

- `ConvenioCard`: inicial, institución, `carrera_destino`, descripción truncada
  (`line-clamp-4`), chips de carreras y botón **“Más info”** (abre el modal).
- Chips: `todas_las_carreras` ⇒ “Todas las carreras”; si no, `carreras[].nombre`.
- `ConvenioDetalleModal`: descripción completa, carreras de origen y botón
  **“Ir al sitio”** → `window.open(link_info, "_blank", "noopener,noreferrer")`.

---

## 5. TalentoTech — estudiante

### 5.1 Pantalla

- Filtro por **categoría** (`<select>`): opciones tomadas de un catálogo acotado
  (`per_page=100`) + la categoría activa. El backend no expone categorías.
- Botón **“Solo mi carrera”** (solo si `usuario.carrera_id != null`) →
  `GET /talentotech/carrera/{id}`.
- Los filtros son mutuamente excluyentes: elegir categoría apaga “Solo mi
  carrera” y viceversa.
- **Sin búsqueda textual** (el backend no soporta `q` en TalentoTech).
- `ListState` + `Paginador`.

### 5.2 Card

`TalentoTechCard` muestra:

- inicial de `nombre_curso`,
- `nombre_curso` + `institucion`,
- badge `categoria` + badge `dificultad` (solo si no es `null`),
- `descripcion` truncada (`line-clamp-4`),
- `duracion` y `modalidad_cursada`,
- disponibilidad (`todas_las_carreras` / chips de `carreras`),
- **“Ver detalle”** (modal) e **“Inscribirme”** (`link_inscripcion` en pestaña
  nueva).

### 5.3 Modal

`TalentoTechDetalleModal`: descripción completa, duración, modalidad,
dificultad (si existe), disponibilidad y CTA **“Inscribirme”**.

---

## 6. Admin — Convenios

- Lista paginada (`getConveniosAdmin`) + `ListState` + `Paginador`.
- `convenioSpec.ts`:

| Campo | Tipo | Reglas |
|---|---|---|
| `institucion` | text | requerido |
| `carrera_destino` | text | requerido |
| `descripcion` | text | requerido |
| `link_info` | url | requerido; `http/https` validado en `aBody` |
| `todas_las_carreras` | switch | — |
| `carrera_ids` | multiselect | requerido si el switch está apagado |

- `aBody`: `trim`, valida URL, exige ≥1 carrera si no es wildcard y **omite**
  `carrera_ids` cuando `todas_las_carreras = true`.
- Alta `POST`; edición `PATCH` (el form envía todos los campos, pero el endpoint
  es parcial); baja `DELETE` + `ConfirmDialog`.
- `onError`: `409 → toast`, `422 → fields`.
- `convenioSpec` **no** define `maxLength` (los límites 150 son de columna).

---

## 7. Admin — TalentoTech

- Opciones de carreras: `useCarreras({ per_page: 100 })`.
- `talentoTechSpec.ts`:

| Campo | Tipo | Reglas |
|---|---|---|
| `institucion` | text | requerido, `maxLength: 150` |
| `nombre_curso` | text | requerido, `maxLength: 150` |
| `categoria` | text | requerido, `maxLength: 20`, texto libre |
| `descripcion` | textarea | requerido |
| `duracion` | text | requerido, `maxLength: 50` |
| `modalidad_cursada` | text | requerido, `maxLength: 50` |
| `dificultad` | text | opcional, `maxLength: 30` |
| `link_inscripcion` | url | requerido; `http/https` validado en `aBody` |
| `todas_las_carreras` | switch | — |
| `carrera_ids` | multiselect | requerido si el switch está apagado |

- `aBody`: valida URL, exige ≥1 carrera si no es wildcard y omite `carrera_ids`
  cuando es wildcard.
- Alta `POST`; edición `PUT` con body completo; baja `DELETE`.
- `onError`: `409 → toast`, `422 → fields`.
- La tabla del admin muestra “Todas las carreras” o chips de `carreras`.

---

## 8. Errores → UI

| Backend | Frontend |
|---|---|
| `401` sin/invalid token | `apiClient` → logout / redirect |
| `403` no admin | `RutaAdmin` redirect + toast |
| `404` | `ListState` error / toast |
| `409` duplicado | toast con `detail` |
| `409` integridad | toast genérico |
| `422` con `errors[]` | `fieldErrors` por campo |
| `422` de dominio (solo `detail`) | toast / mensaje general |

---

## 9. Tests

- `src/features/talentotech/TalentoTechSection.test.tsx`: tab, filtros
  (categoría vs “Solo mi carrera”), card/modal, disponibilidad.
- `src/features/convenios/ConveniosScreen.test.tsx`: listado, chips
  (“Todas las carreras”), cambio de tab a TalentoTech.

---

## 10. Limitaciones conocidas

- **Catálogo de categorías acotado**: se arma con hasta 100 cursos; con más
  cursos puede quedar incompleto. No hay endpoint de categorías.
- **Sin búsqueda en TalentoTech**: no hay `q` en el backend.
- **Sin `PATCH` en TalentoTech**: el admin envía el body completo en cada
  edición.
- **Convenios estudiante sin filtro por carrera**: el servicio lo soporta, la
  pantalla no lo expone.
- **`maxLength` solo en TalentoTech**: `convenioSpec` no los declara; el backend
  tampoco valida longitud en Pydantic (es límite de columna).
- **`dificultad` vacía**: el backend no hace `strip`; `""` y `null` son
  distintos. Para “sin dificultad”, omitir el campo o enviar `null`.
