# Convenios — contrato de API para el front

> Documento para el agente que implementa el front. Reemplaza lo que estaba en
> `INTEGRACION_FRONT.md` §3.4 para la feature **convenios**.
> Última actualización: 2026-10-28.

Base URL: la misma de la API (`VITE_API_URL` o equivalente).
Lectura: **pública**. Escritura: **solo admin** (`Authorization: Bearer <token>`).

---

## 1. Qué cambió respecto de la versión anterior

| Antes | Ahora |
|---|---|
| `carrera_id: number` (una sola carrera de origen) | `carrera_ids: number[]` (una o varias) **o** `todas_las_carreras: true` |
| Respuesta con `carrera_id` | Respuesta con `todas_las_carreras` + `carreras: [{ id, nombre }]` |
| Duplicado por `(carrera_id, institucion, carrera_destino)` | Duplicado por `(institucion, carrera_destino)` |
| Un convenio por carrera | Un convenio puede aplicar a varias carreras de origen sin duplicar filas |

> ⚠️ **Breaking change**: `carrera_id` ya no existe ni en el request ni en la
> respuesta. Si el front lo usaba, tiene que migrar a `carrera_ids` / `carreras`.

El resto del contrato (paginación, `?q=`, orden, `PATCH`) se mantiene.

---

## 2. Modelo de datos

```ts
export interface CarreraResumen {
  id: number;
  nombre: string;
}

export interface Convenio {
  id: number;
  institucion: string;          // ≤ 150, obligatorio
  carrera_destino: string;      // ≤ 150, obligatorio (texto libre)
  descripcion: string;          // obligatorio
  link_info: string;            // URL http/https, obligatorio
  todas_las_carreras: boolean;  // true ⇒ aplica a todas las carreras
  carreras: CarreraResumen[];   // [] cuando todas_las_carreras = true
}

export interface ConvenioCreate {
  institucion: string;
  carrera_destino: string;
  descripcion: string;
  link_info: string;
  carrera_ids?: number[] | null;   // requerido si todas_las_carreras = false
  todas_las_carreras?: boolean;    // default false
}

export interface ConvenioUpdate {  // PATCH — todos opcionales
  institucion?: string;
  carrera_destino?: string;
  descripcion?: string;
  link_info?: string;
  carrera_ids?: number[];          // reemplaza el conjunto completo
  todas_las_carreras?: boolean;
}
```

Notas:

- **`carrera_destino` es el nombre de la carrera de destino** (texto libre). No
  existe `carrera_nombre`: usá `carrera_destino` para mostrar.
- `carreras` son las carreras de **origen** habilitadas. Vienen ordenadas por
  `nombre`.
- **Invariante**:
  - `todas_las_carreras = true` ⇒ `carreras = []` y **no** se envía `carrera_ids`.
  - `todas_las_carreras = false` ⇒ `carrera_ids` con **al menos un id**.
- `carrera_ids` se deduplica automáticamente. Un id inexistente devuelve `422`.
- Para el `<select>` de carreras usá `GET /materias/carreras` (público).
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

Query params de paginación: `page` (≥1) y `per_page` (1–100).

---

## 4. Endpoints

### 4.1 Listar convenios

```http
GET /convenios/?q=&page=1&per_page=20
```

- `q` opcional: busca **case-insensitive** por subcadena en `institucion`,
  `carrera_destino` y `descripcion` (OR entre los tres).
- `q` vacío o ausente: no filtra.
- Orden: `lower(institucion) ASC, id ASC` (alfabético case-insensitive).

Respuesta `200`:

```json
{
  "items": [
    {
      "id": 1,
      "institucion": "Universidad Nacional de General Sarmiento",
      "carrera_destino": "Licenciatura en Sistemas",
      "descripcion": "Convenio de articulación para egresados.",
      "link_info": "https://www.ungs.edu.ar/convenios/ifts",
      "todas_las_carreras": false,
      "carreras": [
        { "id": 1, "nombre": "Tecnicatura Superior en Desarrollo de Software" },
        { "id": 2, "nombre": "Tecnicatura Superior en Análisis de Sistemas" }
      ]
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20,
  "total_pages": 1
}
```

### 4.2 Convenios de una carrera (de origen)

```http
GET /convenios/carrera/{carrera_id}?q=&page=1&per_page=20
```

- Devuelve los convenios **asociados explícitamente** a esa carrera **más** los
  que tienen `todas_las_carreras = true`.
- Un convenio aparece **una sola vez**, aunque tenga varias carreras.
- Mismo formato, `?q=` y orden que 4.1.
- Si la carrera no existe devuelve **lista vacía** (no `404`).

Ejemplo: un convenio con `carrera_ids = [1, 2]` aparece en `/convenios/carrera/1`
y en `/convenios/carrera/2`, pero **no** en `/convenios/carrera/3`. Un convenio
con `todas_las_carreras = true` aparece en cualquier carrera.

### 4.3 Detalle

```http
GET /convenios/{id}
```

- `200` → `Convenio`.
- `404` → `{ "detail": "No se encontró el convenio 42" }`.

### 4.4 Crear (admin)

```http
POST /convenios/
Content-Type: application/json
Authorization: Bearer <token-admin>
```

Con carreras explícitas:

```json
{
  "institucion": "Universidad Nacional de General Sarmiento",
  "carrera_destino": "Licenciatura en Sistemas",
  "descripcion": "Convenio de articulación para egresados.",
  "link_info": "https://www.ungs.edu.ar/convenios/ifts",
  "carrera_ids": [1, 2],
  "todas_las_carreras": false
}
```

Disponible para **todas** las carreras:

```json
{
  "institucion": "Universidad Nacional de General Sarmiento",
  "carrera_destino": "Licenciatura en Sistemas",
  "descripcion": "Convenio abierto a todos los egresados.",
  "link_info": "https://www.ungs.edu.ar/convenios/ifts",
  "todas_las_carreras": true
}
```

- `201` → `Convenio` creado.
- `institucion`, `carrera_destino`, `descripcion` y `link_info` son obligatorios.
- `422` si falta `carrera_ids` con `todas_las_carreras = false`, si se envían
  ambos, si algún id no existe o si `link_info` no es una URL http/https válida.
- `409` si ya existe un convenio con la misma `institucion` + `carrera_destino`
  (aunque cambien las carreras).

### 4.5 Editar parcialmente (admin)

```http
PATCH /convenios/{id}
Authorization: Bearer <token-admin>
```

```json
{ "descripcion": "Texto actualizado" }
```

- Mandá **solo** los campos que cambian. Todos son opcionales.
- `200` → `Convenio` completo actualizado.
- Body `{}` → `200` con el convenio sin cambios (no es error).
- `404` si el id no existe.
- Un `null` explícito se ignora (las columnas son obligatorias).

Reglas de `carrera_ids` / `todas_las_carreras` en `PATCH`:

| Body | Efecto |
|---|---|
| `{ "carrera_ids": [2, 3] }` | Reemplaza el conjunto completo de carreras |
| `{ "todas_las_carreras": true }` | Pasa a wildcard y **borra** las carreras explícitas |
| `{ "todas_las_carreras": false, "carrera_ids": [1] }` | Sale de wildcard con esas carreras |
| `{ "todas_las_carreras": false }` sobre un wildcard sin carreras previas | `422` (debe indicar al menos una) |
| `{ "todas_las_carreras": true, "carrera_ids": [1] }` | `422` (son excluyentes) |

### 4.6 Reemplazar (admin)

```http
PUT /convenios/{id}
```

- Reemplazo total con el mismo contrato que `POST` (incluye `carrera_ids` o
  `todas_las_carreras`).
- `200` → `Convenio` actualizado.

### 4.7 Eliminar (admin)

```http
DELETE /convenios/{id}
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
| `404` | `GET/PATCH/PUT/DELETE` con id inexistente | `{ "detail": "..." }` |
| `409` | Duplicado `(institucion, carrera_destino)` | `{ "detail": "Ya existe un convenio con la misma institución y carrera destino" }` |
| `422` | Carrera(s) inexistente(s) | `{ "detail": "No existen las carreras: 4, 7" }` (o `"No existe la carrera 4"`) |
| `422` | Flag + ids incompatibles / sin carreras | `{ "detail": "..." }` |
| `422` | Error de validación de campos (Pydantic) | `{ "detail": [{ "loc": [...], "msg": "..." }] }` |

> Ojo: hay **dos formas** de `422`. Si `detail` es una lista/estructura de
> validación, conviene pintarla en el formulario. Si `detail` es un string, es
> una regla de dominio y conviene mostrarlo como mensaje general.

---

## 6. Reglas que afectan la UI

1. **Unicidad case-sensitive**: `"UNGS"` y `"ungs"` cuentan como instituciones
   distintas. Los espacios al borde se recortan antes de guardar.
2. **Búsqueda sin acentos**: ni SQLite ni PostgreSQL (sin `unaccent`) pliegan
   acentos. `"tecnologica"` no encuentra `"Tecnológica"`.
3. **`carrera_destino` es texto libre**: no se valida contra el catálogo de
   carreras. Podés cargar "Licenciatura en Sistemas" aunque no exista como
   `Carrera` en la base.
4. **"Disponible para: Todas las carreras"** se muestra cuando
   `todas_las_carreras === true`; en ese caso no listes chips de carreras
   (`carreras` viene vacío). Si es `false`, mostrá los nombres de `carreras`.
5. **Borrar una carrera** con convenios explícitos puede fallar por FK en
   PostgreSQL (la API devuelve `409` genérico). SQLite no fuerza FKs por
   defecto, así que ese control no aplica en desarrollo local.
6. **Listado vacío es `200`**, nunca `404`.
7. Para editar carreras usá `PATCH` con `carrera_ids` completo (no hay endpoint
   para agregar/quitar una sola).

---

## 7. Ejemplos de uso (cliente HTTP)

```ts
// Listar con búsqueda
const res = await fetch(`${API}/convenios/?q=ungs&page=1&per_page=20`);
const page: Paginated<Convenio> = await res.json();

// Convenios disponibles para la carrera del alumno (incluye wildcard)
const porCarrera = await fetch(`${API}/convenios/carrera/${carreraId}?q=`);
const disponibles: Paginated<Convenio> = await porCarrera.json();

// Crear para dos carreras de origen
await fetch(`${API}/convenios/`, {
  method: "POST",
  headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  body: JSON.stringify({
    institucion: "UNGS",
    carrera_destino: "Licenciatura en Sistemas",
    descripcion: "Articulación",
    link_info: "https://www.ungs.edu.ar/convenio",
    carrera_ids: [1, 2],
  }),
});

// Crear para todas las carreras
await fetch(`${API}/convenios/`, {
  method: "POST",
  headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  body: JSON.stringify({
    institucion: "UNGS",
    carrera_destino: "Licenciatura en Sistemas",
    descripcion: "Abierto a todos",
    link_info: "https://www.ungs.edu.ar/convenio",
    todas_las_carreras: true,
  }),
});

// Editar solo la descripción
await fetch(`${API}/convenios/${id}`, {
  method: "PATCH",
  headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  body: JSON.stringify({ descripcion: "Nueva descripción" }),
});
```

---

## 8. Checklist de integración

- [ ] Tipos `Convenio`, `ConvenioCreate`, `ConvenioUpdate`, `CarreraResumen`,
      `Paginated<T>`.
- [ ] Eliminar cualquier uso de `carrera_id` en convenios.
- [ ] Listado con `page` / `per_page` y paginador usando `total_pages`.
- [ ] Buscador conectado a `q` (debounce sugerido).
- [ ] Detalle por id con manejo de `404`.
- [ ] Formulario de alta (admin) con selector **múltiple** de carreras o check
      "Todas las carreras" (excluyentes).
- [ ] Formulario de edición (admin) usando `PATCH`; al cambiar carreras enviar
      el array completo `carrera_ids`.
- [ ] Mostrar chips con `carreras[].nombre`, u "Todas las carreras" cuando
      `todas_las_carreras === true`.
- [ ] Manejo diferenciado de `422` de validación vs. `422` de dominio.
- [ ] Mostrar `detail` en `409` (duplicado) y `422` (carreras inexistentes).
- [ ] Acciones de escritura ocultas para rol `estudiante`.
