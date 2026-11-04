# TalentoTech — contrato de API para el front

> Documento para el agente que implementa el front. Reemplaza la referencia
> genérica de `INTEGRACION_FRONT.md` §3.4 para la feature **TalentoTech**.
> Última actualización: 2026-11-03.
> Spec completa: `docs/openapi.json`. Datos cargados: `docs/DATA_TALENTOTECH.md`.

Base URL: la misma de la API (`VITE_API_URL` o equivalente).
Lectura: **pública**. Escritura: **solo admin** (`Authorization: Bearer <token>`).

---

## 1. Qué cambió respecto de la versión anterior

| Antes | Ahora |
|---|---|
| `carrera_id: number` (una sola carrera) | `carrera_ids: number[]` (una o varias) **o** `todas_las_carreras: true` |
| Respuesta con `carrera_id` | Respuesta con `todas_las_carreras` + `carreras: [{ id, nombre }]` |
| Sin `institucion` | `institucion` obligatoria |
| Sin `modalidad_cursada` en la respuesta | `modalidad_cursada` obligatoria y presente en la respuesta |
| `dificultad` obligatoria y no persistida | `dificultad` **opcional** (`string \| null`) y persistida |
| `TalentoTechResponse` heredaba del request | Respuesta explícita, con `id` y `carreras` (lista para la card) |
| Duplicado libre | Duplicado por `(institucion, nombre_curso)` → `409` |

> ⚠️ **Breaking change**: `carrera_id` ya no existe ni en el request ni en la
> respuesta. Si el front lo usaba, tiene que migrar a `carrera_ids` /
> `carreras`. Tampoco existe `PATCH`: la edición es `PUT` (reemplazo total).

---

## 2. Modelo de datos

```ts
export interface CarreraResumen {
  id: number;
  nombre: string;
}

export interface TalentoTech {
  id: number;
  institucion: string;           // obligatorio
  nombre_curso: string;          // obligatorio
  categoria: string;             // obligatorio (texto libre, no catálogo)
  descripcion: string;           // obligatorio
  duracion: string;              // obligatorio (texto libre, ej. "30hs")
  modalidad_cursada: string;     // obligatorio (texto libre)
  dificultad: string | null;     // opcional
  link_inscripcion: string;      // URL http/https
  todas_las_carreras: boolean;   // true ⇒ aplica a todas las carreras
  carreras: CarreraResumen[];    // [] cuando todas_las_carreras = true
}

export interface TalentoTechCreate {
  institucion: string;
  nombre_curso: string;
  categoria: string;
  descripcion: string;
  duracion: string;
  modalidad_cursada: string;
  dificultad?: string | null;      // opcional
  link_inscripcion: string;        // http/https
  carrera_ids?: number[] | null;   // requerido si todas_las_carreras = false
  todas_las_carreras?: boolean;    // default false
}
```

Notas:

- **No hay `TalentoTechUpdate`**: `PUT` usa el mismo body que `POST` (todos los
  campos obligatorios, salvo `dificultad`).
- **Invariante**:
  - `todas_las_carreras = true` ⇒ `carreras = []` y **no** se envía `carrera_ids`.
  - `todas_las_carreras = false` ⇒ `carrera_ids` con **al menos un id**.
- `carrera_ids` se deduplica automáticamente. Un id inexistente devuelve `422`.
- `carreras` son las carreras de **origen** habilitadas, ordenadas por `nombre`.
- Para el `<select>` de carreras usá `GET /materias/carreras` (público).
- `categoria` es **texto libre** (no hay endpoint de categorías). El filtro por
  categoría es por **igualdad exacta y case-sensitive**.
- Límites de columna (PostgreSQL los aplica; respetalos en el formulario):
  `institucion` y `nombre_curso` ≤ 150, `categoria` ≤ 20, `duracion` y
  `modalidad_cursada` ≤ 50, `dificultad` ≤ 30.
- No hay `created_at` ni `updated_at`.

---

## 3. Envoltorio paginado

Todos los listados devuelven:

```ts
export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;      // default 20, máximo 100
  total_pages: number;
}
```

Query params: `page` (≥1) y `per_page` (1–100).

---

## 4. Endpoints

### 4.1 Listar cursos

```http
GET /talentotech/?page=1&per_page=20
```

- Orden: `lower(nombre_curso) ASC, id ASC` (alfabético case-insensitive).
- **No hay búsqueda `q`** en TalentoTech. Si el front necesita buscar, por ahora
  se filtra del lado del cliente sobre los `items` recibidos.

Respuesta `200`:

```json
{
  "items": [
    {
      "id": 1,
      "institucion": "Agencia de Habilidades para el Futuro",
      "nombre_curso": "Tecnologías Emergentes",
      "categoria": "IT",
      "descripcion": "En este curso te sumergirás en aquellas revoluciones...",
      "duracion": "30hs",
      "modalidad_cursada": "Virtual Asincrónico",
      "dificultad": null,
      "link_inscripcion": "https://talentotech.bue.edu.ar/home/inscripcion/adultos",
      "todas_las_carreras": true,
      "carreras": []
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20,
  "total_pages": 1
}
```

### 4.2 Cursos de una carrera (de origen)

```http
GET /talentotech/carrera/{carrera_id}?page=1&per_page=20
```

- Devuelve los cursos **asociados explícitamente** a esa carrera **más** los que
  tienen `todas_las_carreras = true`.
- Un curso aparece **una sola vez**, aunque tenga varias carreras.
- Mismo formato y orden que 4.1.
- Si la carrera no existe devuelve **lista vacía** (no `404`).
- Es el endpoint natural para "cursos disponibles para mi carrera".

Ejemplo: un curso con `carrera_ids = [1, 2]` aparece en `/talentotech/carrera/1`
y en `/talentotech/carrera/2`, pero **no** en `/talentotech/carrera/3`. Un curso
con `todas_las_carreras = true` aparece en cualquier carrera existente.

### 4.3 Cursos de una categoría

```http
GET /talentotech/categoria/{categoria}?page=1&per_page=20
```

- Filtro por **igualdad exacta** (`IT` ≠ `it`), sin comodines.
- Mismo formato y orden que 4.1.
- Categoría sin cursos → lista vacía `200`.

### 4.4 Detalle

```http
GET /talentotech/{id}
```

- `200` → `TalentoTech`.
- `404` → `{ "detail": "No se encontró el talentotech con ID: 42" }`.
- Ojo con el orden de rutas: `/carrera/...` y `/categoria/...` tienen prioridad;
  el `{id}` es numérico.

### 4.5 Crear (admin)

```http
POST /talentotech/
Content-Type: application/json
Authorization: Bearer <token-admin>
```

Con carreras explícitas (una o varias):

```json
{
  "institucion": "Agencia de Habilidades para el Futuro",
  "nombre_curso": "Tecnologías Emergentes",
  "categoria": "IT",
  "descripcion": "Curso introductorio a las tecnologías emergentes.",
  "duracion": "30hs",
  "modalidad_cursada": "Virtual Asincrónico",
  "dificultad": "Introductoria",
  "link_inscripcion": "https://talentotech.bue.edu.ar/home/inscripcion/adultos",
  "carrera_ids": [1, 3],
  "todas_las_carreras": false
}
```

Disponible para **todas** las carreras:

```json
{
  "institucion": "Agencia de Habilidades para el Futuro",
  "nombre_curso": "Tecnologías Emergentes",
  "categoria": "IT",
  "descripcion": "Curso introductorio a las tecnologías emergentes.",
  "duracion": "30hs",
  "modalidad_cursada": "Virtual Asincrónico",
  "link_inscripcion": "https://talentotech.bue.edu.ar/home/inscripcion/adultos",
  "todas_las_carreras": true
}
```

- `201` → `TalentoTech` creado (con `id`, `todas_las_carreras` y `carreras`).
- `422` si falta `carrera_ids` con `todas_las_carreras = false`, si se envían
  ambos, si algún id no existe o si `link_inscripcion` no es una URL http/https.
- `409` si ya existe un curso con la misma `institucion` + `nombre_curso`
  (aunque cambien las carreras).

### 4.6 Reemplazar (admin)

```http
PUT /talentotech/{id}
Authorization: Bearer <token-admin>
```

- **Reemplazo total**: mismo body que `POST` (todos los campos). No hay `PATCH`.
- Si el curso era wildcard y se envía `carrera_ids`, pasa a carreras explícitas
  (y viceversa: `todas_las_carreras: true` **borra** las carreras explícitas).
- `200` → `TalentoTech` actualizado.
- `404` si el id no existe.

### 4.7 Eliminar (admin)

```http
DELETE /talentotech/{id}
```

- `204` sin body.
- `404` si el id no existe.
- Elimina también las asociaciones con carreras.

---

## 5. Códigos de error

| Código | Cuándo | Cuerpo |
|---|---|---|
| `401` | Escritura sin token | `{ "detail": "No autenticado" }` |
| `403` | Escritura con token de estudiante | `{ "detail": "No tenés permiso para esta operación" }` |
| `404` | `GET/PUT/DELETE` con id inexistente | `{ "detail": "No se encontró el talentotech con ID: 42" }` |
| `409` | Duplicado `(institucion, nombre_curso)` | `{ "detail": "Ya existe un curso TalentoTech con la misma institución y nombre" }` |
| `409` | Violación de integridad no controlada (p. ej. borrar una carrera con cursos explícitos en Postgres) | `{ "detail": "Conflicto de integridad de datos" }` |
| `422` | Carrera(s) inexistente(s) | `{ "detail": "No existen las carreras: 4, 7" }` (o `"No existe la carrera 4"`) |
| `422` | `todas_las_carreras: true` + `carrera_ids` | `{ "detail": "Si 'todas_las_carreras' es true no se debe enviar 'carrera_ids'" }` |
| `422` | Sin carreras y sin flag | `{ "detail": "Debe indicar al menos una carrera en 'carrera_ids' o marcar 'todas_las_carreras'" }` |
| `422` | Error de validación de campos (Pydantic) | `{ "detail": "<primer mensaje>", "errors": [{ "campo": "link_inscripcion", "msg": "..." }] }` |

> **Formato de los `422`**: `detail` es **siempre un string** (apto para mostrar
> como mensaje general). En los errores de validación de campos viene además
> `errors: [{ campo, msg }]` con el detalle por campo, que podés mapear al
> formulario. Las reglas de dominio (carreras inexistentes, flag/ids) traen solo
> `detail`.

---

## 6. Reglas que afectan la UI

1. **Unicidad case-sensitive**: `"IT"` y `"it"` son categorías distintas, y
   `"Curso X"` y `"curso x"` son cursos distintos. Los espacios al borde de los
   campos de texto se recortan antes de guardar.
2. **Sin plegado de acentos**: `"tecnologias"` no encuentra `"Tecnologías"`.
3. **`categoria` es texto libre**: no se valida contra un catálogo. Si querés un
   `<select>`, definí las opciones en el front (hoy: `"IT"`).
4. **`modalidad_cursada` es texto libre**: hoy el curso cargado tiene
   `"Virtual Asincrónico"`. No asumas un enum.
5. **`dificultad` puede ser `null`**: ocultá el badge si viene vacío.
6. **"Disponible para: Todas las carreras"** se muestra cuando
   `todas_las_carreras === true`; en ese caso no listes chips de carreras
   (`carreras` viene vacío). Si es `false`, mostrá los nombres de `carreras`.
7. **Listado vacío es `200`**, nunca `404` (incluida una carrera inexistente).
8. **`PUT` exige el objeto completo**: no sirve para mandar un solo campo. Para
   editar la descripción, enviá también institución, curso, categoría, duración,
   modalidad, link y `carrera_ids`/`todas_las_carreras`.
9. **Borrar una carrera** con cursos explícitos puede fallar por FK en
   PostgreSQL (la API devuelve `409` genérico). SQLite no fuerza FKs por
   defecto, así que ese control no aplica en desarrollo local.
10. **Un curso wildcard aparece en todas las carreras**, incluida cualquier
    carrera nueva que se cree después.

---

## 7. Mapeo sugerido para la card

| Elemento de la card | Campo |
|---|---|
| Título | `nombre_curso` |
| Institución / emisor | `institucion` |
| Badge / etiqueta | `categoria` |
| Texto | `descripcion` (truncar con CSS, p. ej. 3 líneas) |
| Duración | `duracion` |
| Modalidad | `modalidad_cursada` |
| Nivel (opcional) | `dificultad` (si no es `null`) |
| CTA "Inscribirme" | `link_inscripcion` (`target="_blank" rel="noopener noreferrer"`) |
| Disponibilidad | `todas_las_carreras ? "Todas las carreras" : carreras.map(c => c.nombre)` |

---

## 8. Ejemplos de uso (cliente HTTP)

```ts
// Listar todos (paginado)
const res = await fetch(`${API}/talentotech/?page=1&per_page=20`);
const page: Paginated<TalentoTech> = await res.json();

// Cursos disponibles para la carrera del alumno (incluye wildcard)
const porCarrera = await fetch(`${API}/talentotech/carrera/${carreraId}?per_page=100`);
const disponibles: Paginated<TalentoTech> = await porCarrera.json();

// Filtrar por categoría (igualdad exacta)
const it = await fetch(`${API}/talentotech/categoria/IT?per_page=100`);
const cursosIT: Paginated<TalentoTech> = await it.json();

// Crear para dos carreras de origen
await fetch(`${API}/talentotech/`, {
  method: "POST",
  headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  body: JSON.stringify({
    institucion: "Agencia de Habilidades para el Futuro",
    nombre_curso: "Tecnologías Emergentes",
    categoria: "IT",
    descripcion: "Curso introductorio.",
    duracion: "30hs",
    modalidad_cursada: "Virtual Asincrónico",
    link_inscripcion: "https://talentotech.bue.edu.ar/home/inscripcion/adultos",
    carrera_ids: [1, 3],
  }),
});

// Crear para todas las carreras
await fetch(`${API}/talentotech/`, {
  method: "POST",
  headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  body: JSON.stringify({
    institucion: "Agencia de Habilidades para el Futuro",
    nombre_curso: "Tecnologías Emergentes",
    categoria: "IT",
    descripcion: "Curso introductorio.",
    duracion: "30hs",
    modalidad_cursada: "Virtual Asincrónico",
    link_inscripcion: "https://talentotech.bue.edu.ar/home/inscripcion/adultos",
    todas_las_carreras: true,
  }),
});

// Reemplazar (PUT: body completo)
await fetch(`${API}/talentotech/${id}`, {
  method: "PUT",
  headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  body: JSON.stringify({ ...cursoActual, descripcion: "Nueva descripción" }),
});
```

---

## 9. Checklist de integración

- [ ] Tipos `TalentoTech`, `TalentoTechCreate`, `CarreraResumen`, `Paginated<T>`.
- [ ] Eliminar cualquier uso de `carrera_id` en TalentoTech.
- [ ] Listado con `page` / `per_page` y paginador usando `total_pages`.
- [ ] Vista "cursos de mi carrera" usando `/talentotech/carrera/{carrera_id}`.
- [ ] Filtro por categoría con `/talentotech/categoria/{categoria}` (match exacto).
- [ ] Detalle por id con manejo de `404`.
- [ ] Formulario de alta (admin) con selector **múltiple** de carreras o check
      "Todas las carreras" (excluyentes).
- [ ] Formulario de edición (admin) con `PUT` completo (no `PATCH`).
- [ ] Mostrar chips con `carreras[].nombre`, o "Todas las carreras" cuando
      `todas_las_carreras === true`.
- [ ] Ocultar `dificultad` cuando sea `null`.
- [ ] CTA de inscripción abriendo `link_inscripcion` en pestaña nueva.
- [ ] Manejo de `422`: usar `errors[]` para marcar campos y `detail` para el mensaje general.
- [ ] Mostrar `detail` en `409` (duplicado).
- [ ] Acciones de escritura ocultas para rol `estudiante`.
