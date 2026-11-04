# Convenios + TalentoTech — Contrato API

> Última actualización: 2026-11-04 (N:M con carreras de origen, `todas_las_carreras`,
> `PATCH` en convenios, búsqueda `q`, card de TalentoTech).
> Contratos detallados: `docs/CONVENIOS_FRONT.md` y `docs/TALENTOTECH_FRONT.md`.
> Spec generada: `docs/openapi.json`.

Base URL: la de la API (`VITE_API_URL` o equivalente).
Lectura: **pública**. Escritura: **solo admin** (`Authorization: Bearer <token>`).

---

## 1. Tipos

```typescript
interface CarreraResumen {
  id: number;
  nombre: string;
}

// ---------- Convenios ----------
interface ConvenioCreate {
  institucion: string;              // obligatorio, límite de columna 150
  carrera_destino: string;          // obligatorio, límite de columna 150 (texto libre)
  descripcion: string;              // obligatorio
  link_info: string;                // obligatorio, HttpUrl (http/https)
  carrera_ids?: number[] | null;    // requerido si todas_las_carreras = false
  todas_las_carreras?: boolean;     // default false
}

interface ConvenioUpdate {          // PATCH — todos opcionales
  institucion?: string;
  carrera_destino?: string;
  descripcion?: string;
  link_info?: string;
  carrera_ids?: number[];           // reemplaza el conjunto completo
  todas_las_carreras?: boolean;
}

interface ConvenioResponse {
  id: number;
  institucion: string;
  carrera_destino: string;
  descripcion: string;
  link_info: string;
  todas_las_carreras: boolean;      // true ⇒ aplica a todas las carreras
  carreras: CarreraResumen[];       // [] cuando todas_las_carreras = true
}

// ---------- TalentoTech ----------
interface TalentoTechCreate {
  institucion: string;              // obligatorio, límite de columna 150
  nombre_curso: string;             // obligatorio, límite de columna 150
  categoria: string;                // obligatorio, límite de columna 20 (texto libre)
  descripcion: string;              // obligatorio
  duracion: string;                 // obligatorio, límite de columna 50 (texto libre)
  modalidad_cursada: string;        // obligatorio, límite de columna 50 (texto libre)
  dificultad?: string | null;       // opcional, límite de columna 30
  link_inscripcion: string;         // obligatorio, HttpUrl (http/https)
  carrera_ids?: number[] | null;    // requerido si todas_las_carreras = false
  todas_las_carreras?: boolean;     // default false
}

interface TalentoTechResponse {
  id: number;
  institucion: string;
  nombre_curso: string;
  categoria: string;
  descripcion: string;
  duracion: string;
  modalidad_cursada: string;
  dificultad: string | null;
  link_inscripcion: string;
  todas_las_carreras: boolean;
  carreras: CarreraResumen[];       // [] cuando todas_las_carreras = true
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;                 // default 20, máximo 100
  total_pages: number;
}
```

> **No existe `TalentoTechUpdate`**: el `PUT` de TalentoTech usa el mismo body
> que el `POST`. Convenios sí tiene `ConvenioUpdate` para `PATCH`.

---

## 2. Endpoints

### 2.1 Convenios

| Método | Ruta | Auth | Body / params | Response |
|---|---|---|---|---|
| `GET` | `/convenios/` | Pública | `q`, `page`, `per_page` | `200 PaginatedResponse<ConvenioResponse>` |
| `GET` | `/convenios/carrera/{carrera_id}` | Pública | `q`, `page`, `per_page` | `200 PaginatedResponse<ConvenioResponse>` |
| `GET` | `/convenios/{id}` | Pública | — | `200 ConvenioResponse` / `404` |
| `POST` | `/convenios/` | **Admin** | `ConvenioCreate` | `201 ConvenioResponse` |
| `PUT` | `/convenios/{id}` | **Admin** | `ConvenioCreate` (completo) | `200 ConvenioResponse` / `404` |
| `PATCH` | `/convenios/{id}` | **Admin** | `ConvenioUpdate` (parcial) | `200 ConvenioResponse` / `404` |
| `DELETE` | `/convenios/{id}` | **Admin** | — | `204` sin body / `404` |

### 2.2 TalentoTech

| Método | Ruta | Auth | Body / params | Response |
|---|---|---|---|---|
| `GET` | `/talentotech/` | Pública | `page`, `per_page` | `200 PaginatedResponse<TalentoTechResponse>` |
| `GET` | `/talentotech/carrera/{carrera_id}` | Pública | `page`, `per_page` | `200 PaginatedResponse<TalentoTechResponse>` |
| `GET` | `/talentotech/categoria/{categoria}` | Pública | `page`, `per_page` (match exacto) | `200 PaginatedResponse<TalentoTechResponse>` |
| `GET` | `/talentotech/{id}` | Pública | — | `200 TalentoTechResponse` / `404` |
| `POST` | `/talentotech/` | **Admin** | `TalentoTechCreate` | `201 TalentoTechResponse` |
| `PUT` | `/talentotech/{id}` | **Admin** | `TalentoTechCreate` (completo) | `200 TalentoTechResponse` / `404` |
| `DELETE` | `/talentotech/{id}` | **Admin** | — | `204` sin body / `404` |

> TalentoTech **no tiene `PATCH`**.

---

## 3. Reglas del contrato

### 3.1 Carreras de origen (ambas features)

- `todas_las_carreras = true` ⇒ `carreras = []` y **no** se envía `carrera_ids`.
- `todas_las_carreras = false` (o ausente) ⇒ `carrera_ids` con **al menos un id existente**.
- `carrera_ids` se deduplica preservando el orden.
- Un id inexistente ⇒ `422` con el detalle de los faltantes.
- `GET .../carrera/{id}` devuelve los recursos **explícitos** de esa carrera **más**
  los wildcard, sin duplicar filas. Si la carrera no existe ⇒ lista vacía `200`
  (aunque haya wildcard).
- Las carreras se devuelven ordenadas por `nombre`.

### 3.2 Unicidad y orden

| Feature | Clave única | Orden de los listados |
|---|---|---|
| Convenios | `(institucion, carrera_destino)` | `lower(institucion) ASC, id ASC` |
| TalentoTech | `(institucion, nombre_curso)` | `lower(nombre_curso) ASC, id ASC` |

- La comparación de unicidad es **case-sensitive** y no pliega acentos.
- Los textos obligatorios se recortan (`strip`) antes de validar/guardar.

### 3.3 Búsqueda (`q`) — solo Convenios

- `GET /convenios/` y `GET /convenios/carrera/{id}` aceptan `?q=`.
- Busca por subcadena **case-insensitive** (`ILIKE`) en `institucion`,
  `carrera_destino` y `descripcion` (OR entre los tres).
- `q` vacío o ausente no filtra.
- TalentoTech **no tiene búsqueda textual**.

### 3.4 Otros

- Listado vacío ⇒ `200`, nunca `404`.
- TalentoTech filtra por categoría con **igualdad exacta y case-sensitive**
  (`IT` ≠ `it`). No existe `GET /talentotech/categorias`.
- Ninguna de las dos tablas tiene `created_at` / `updated_at`.
- Los límites 150/20/50/30 son de columna: en PostgreSQL se aplican; Pydantic no
  valida `max_length`. El formulario debe prevenirlos.

---

## 4. Ejemplos

### 4.1 Crear convenio con carreras explícitas

```http
POST /convenios/
Authorization: Bearer <admin_token>
Content-Type: application/json
```

```json
{
  "institucion": "Universidad Nacional de Lomas de Zamora",
  "carrera_destino": "Licenciatura en Sistemas",
  "descripcion": "Convenio de articulación para egresados.",
  "link_info": "https://ingenieria.unlz.edu.ar/oferta-academica/grado",
  "carrera_ids": [1, 2]
}
```

### 4.2 Crear convenio para todas las carreras

```json
{
  "institucion": "Universidad Nacional de General Sarmiento",
  "carrera_destino": "Licenciatura en Sistemas",
  "descripcion": "Convenio abierto a todos los egresados.",
  "link_info": "https://www.ungs.edu.ar/convenios/ifts",
  "todas_las_carreras": true
}
```

### 4.3 Editar parcialmente un convenio (PATCH)

```http
PATCH /convenios/{id}
Authorization: Bearer <admin_token>
```

```json
{ "descripcion": "Texto actualizado" }
```

Efecto de los campos de carreras en `PATCH`:

| Body | Efecto |
|---|---|
| `{ "carrera_ids": [2, 3] }` | Reemplaza el conjunto completo (sobre un convenio **no** wildcard) |
| `{ "carrera_ids": [2, 3] }` sobre un wildcard | `422` (primero hay que bajar `todas_las_carreras`) |
| `{ "todas_las_carreras": true }` | Pasa a wildcard y **borra** las carreras explícitas |
| `{ "todas_las_carreras": false, "carrera_ids": [1] }` | Sale de wildcard con esas carreras |
| `{ "todas_las_carreras": false }` sobre un wildcard | `422` (debe indicar al menos una) |
| `{ "todas_las_carreras": true, "carrera_ids": [1] }` | `422` (excluyentes) |

### 4.4 Listar convenios con búsqueda

```http
GET /convenios/?q=ungs&page=1&per_page=20
```

### 4.5 Convenios de una carrera (incluye wildcard)

```http
GET /convenios/carrera/2?q=&page=1&per_page=20
```

### 4.6 Crear curso TalentoTech para todas las carreras

```http
POST /talentotech/
Authorization: Bearer <admin_token>
```

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

### 4.7 Crear curso TalentoTech para varias carreras

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
  "carrera_ids": [1, 3]
}
```

### 4.8 Reemplazar un curso (PUT completo)

```http
PUT /talentotech/{id}
Authorization: Bearer <admin_token>
```

Body: mismo shape que `4.6`/`4.7` (todos los campos; `dificultad` opcional).
Pasar a `todas_las_carreras: true` borra las carreras explícitas.

### 4.9 Listar cursos

```http
GET /talentotech/?page=1&per_page=20
GET /talentotech/carrera/2?per_page=100
GET /talentotech/categoria/IT?per_page=100
```

---

## 5. Códigos de error

| Código | Cuándo | Body |
|---|---|---|
| `401` | Falta el header `Authorization` | `{ "detail": "Not authenticated" }` |
| `401` | Token inválido o expirado | `{ "detail": "Token inválido o expirado" }` |
| `403` | Token de estudiante en `POST`/`PUT`/`PATCH`/`DELETE` | `{ "detail": "Se requieren permisos de administrador" }` |
| `404` | Convenio inexistente | `{ "detail": "No se encontró el convenio 42" }` |
| `404` | Curso TalentoTech inexistente | `{ "detail": "No se encontró el talentotech con ID: 42" }` |
| `409` | Duplicado `(institucion, carrera_destino)` | `{ "detail": "Ya existe un convenio con la misma institución y carrera destino" }` |
| `409` | Duplicado `(institucion, nombre_curso)` | `{ "detail": "Ya existe un curso TalentoTech con la misma institución y nombre" }` |
| `409` | Integridad no controlada (p. ej. FK al borrar una carrera en Postgres) | `{ "detail": "Conflicto de integridad de datos" }` |
| `422` | Carrera(s) inexistente(s) | `{ "detail": "No existe la carrera 4" }` / `{ "detail": "No existen las carreras: 4, 7" }` |
| `422` | `todas_las_carreras: true` + `carrera_ids` no vacío | `{ "detail": "Si 'todas_las_carreras' es true no se debe enviar 'carrera_ids'" }` |
| `422` | Sin carreras y sin flag | `{ "detail": "Debe indicar al menos una carrera en 'carrera_ids' o marcar 'todas_las_carreras'" }` |
| `422` | Error de validación de Pydantic | `{ "detail": "<primer mensaje>", "errors": [{ "campo": "...", "msg": "..." }] }` |

> `detail` es **siempre un string**. Solo los `422` de Pydantic agregan
> `errors[]` con el detalle por campo.

---

## 6. Servicios del frontend

```typescript
// Estudiante — convenios (features/convenios/service.ts)
getConvenios({ page?, per_page?, q?, carrera_id? })
  // carrera_id ≠ null → GET /convenios/carrera/{id}
  // caso contrario      → GET /convenios/

// Estudiante — TalentoTech (features/talentotech/service.ts)
getTalentoTech({ page?, per_page?, categoria?, carrera_id? })
  // prioridad: categoria > carrera_id > listado completo

// Admin — convenios (features/convenios-admin/service.ts)
getConveniosAdmin({ page?, per_page?, q? })
crearConvenio(body)          // POST   /convenios/
editarConvenio(id, body)     // PATCH  /convenios/{id}
borrarConvenio(id)           // DELETE /convenios/{id}

// Admin — TalentoTech (features/talentotech-admin/service.ts)
getTalentoTechAdmin({ page?, per_page? })
crearTalentoTech(body)       // POST   /talentotech/
editarTalentoTech(id, body)  // PUT    /talentotech/{id}  (body completo)
borrarTalentoTech(id)        // DELETE /talentotech/{id}
```

> El admin de convenios usa `PATCH`; el de TalentoTech usa `PUT` porque el
> backend no expone `PATCH` para cursos.

---

## 7. Referencias

- Contrato detallado de convenios: `docs/CONVENIOS_FRONT.md`
- Contrato detallado de TalentoTech: `docs/TALENTOTECH_FRONT.md`
- Datos cargados: `docs/DATA_CONVENIOS.md`, `docs/DATA_TALENTOTECH.md`
- Spec OpenAPI: `docs/openapi.json` (`python scripts/export_openapi.py`)
