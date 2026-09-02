# Integración Front ↔ Backend miIFTS

Cómo consumir la API tal como está construida hoy. Fuente de verdad viva:
`GET /openapi.json` y Swagger en `/docs`.

- **Base URL (dev):** `http://localhost:8000` (uvicorn). Configurable por
  `VITE_API_URL`.
- **CORS:** por defecto acepta `http://localhost:5173` y `http://127.0.0.1:5173`
  (puerto default de Vite). Para otro origen hay que agregarlo a `CORS_ORIGINS`
  en el backend.
- **Formato:** todo JSON. Fechas ISO 8601.

---

## 1. Convenciones globales

### 1.1 Shape de respuestas

| Caso | Forma |
|------|-------|
| **Colección** (todo `GET` que lista) | `{ items: T[], total, page, per_page, total_pages }` |
| **Recurso** (`GET`/`POST`/`PUT`/`PATCH` de un ítem) | objeto plano `T` |
| **DELETE** | `204` sin body |
| **Error** | `{ detail: string }` |
| **Error de validación (`422`)** | `{ detail: string, errors: { campo: string, msg: string }[] }` |

`detail` es **siempre** un string → mostrarlo tal cual en un toast.
En formularios, usar `errors[]` para marcar cada campo (`campo` es el nombre del
field; en anidados viene con punto, ej. `"requiere.codigo"`).

### 1.2 Paginación

**Todos** los listados aceptan:

| Query param | Default | Rango |
|-------------|---------|-------|
| `page` | `1` | ≥ 1 |
| `per_page` | `20` | 1–100 |

Pedir una página fuera de rango devuelve `items: []` con el `total` real.
Para paginar en el front: `total_pages` te dice cuántas hay.

### 1.3 Códigos de estado

| Código | Cuándo | Qué hace el front |
|--------|--------|-------------------|
| `200` | OK (GET/PUT/PATCH) | — |
| `201` | Creado (POST) | — |
| `204` | Borrado (DELETE) | no parsear body |
| `401` | Sin token o token inválido/expirado | limpiar sesión → ir a login |
| `403` | Rol insuficiente / recurso de otro usuario | “no tenés permiso” |
| `404` | No existe | pantalla/estado “no encontrado” |
| `409` | Duplicado o regla de negocio (ej. borrar carrera con materias) | mostrar `detail` |
| `422` | Validación | pintar `errors[]` en el form |

---

## 2. Autenticación

JWT Bearer, HS256, expira a las **24 h**. No hay refresh token ni logout de
servidor: “cerrar sesión” = borrar el token del cliente.

### 2.1 Registro

`POST /auth/registro` — **público**

```jsonc
// request
{ "nombre": "Ada Lovelace", "email": "ada@ifts.edu.ar",
  "password": "secreta123", "carrera_id": 1 }
// 201 -> UsuarioResponse (NO devuelve token)
```

- `password`: mínimo 8, **al menos una letra y un número**.
- `nombre`: 2–100 caracteres.
- `carrera_id`: tiene que existir → conseguí la lista con
  `GET /materias/carreras` (público) para armar el `<select>`.
- El campo `rol` se ignora: siempre se crea `estudiante`.
- Después del registro → hacer login (o auto-login reusando las credenciales).

### 2.2 Login

`POST /auth/login` — **público**

```jsonc
// request
{ "email": "ada@ifts.edu.ar", "password": "secreta123" }
// 200 -> TokenResponse
{ "access_token": "eyJ...", "token_type": "bearer",
  "usuario": { "id": 1, "nombre": "...", "email": "...", "carrera_id": 1,
               "fecha_registro": "2026-09-02T12:00:00", "rol": "estudiante" } }
```

El login ya trae el `usuario` → no hace falta llamar a `/auth/me` después.
Credenciales inválidas → `401` `{ "detail": "Email o contraseña incorrectos" }`.

### 2.3 Usar el token

- Guardarlo (memoria + `localStorage`, o cookie). Guardar también `usuario`.
- Header en cada request autenticado: `Authorization: Bearer <access_token>`.
- Interceptor: si una respuesta es `401` → borrar token + `usuario` y redirigir a
  login (el token venció o es inválido).

### 2.4 Endpoints de sesión

| Método | Path | Auth | Respuesta |
|--------|------|------|-----------|
| `GET` | `/auth/me` | Bearer | `UsuarioResponse` |
| `GET` | `/auth/verify` | Bearer | `{ valid: true, user_id: number }` |

### 2.5 Roles

- `estudiante`: default. Gestiona lo suyo (cursadas, recursos, recordatorios).
- `admin`: además administra el catálogo (carreras y materias).
- El front puede usar `usuario.rol` para mostrar/ocultar el ABM de catálogo,
  pero la autorización real la hace el backend (`403` si corresponde).

---

## 3. Referencia de endpoints

Convención: **Pub** = sin token · **Auth** = Bearer · **Admin** = Bearer + rol admin.

### 3.1 Catálogo académico

| Método | Path | Acceso | Notas |
|--------|------|--------|-------|
| `GET` | `/materias/carreras` | Pub | paginado → `CarreraResponse` |
| `POST` | `/materias/carreras` | Admin | `CarreraCreate` |
| `PUT` | `/materias/carreras/{id}` | Admin | `CarreraUpdate` (parcial) |
| `DELETE` | `/materias/carreras/{id}` | Admin | `409` si la carrera tiene materias |
| `GET` | `/materias/carrera/{carrera_id}` | Pub | materias de una carrera, paginado → `MateriaResponse` |
| `GET` | `/materias/buscar?q=` | Pub | `q` **requerido**; opcionales `anio`, `cuatrimestre`. Paginado → `MateriaResponse` |
| `GET` | `/materias/correlativas/{materia_id}` | Pub | paginado → `CorrelativaResponse` (trae la materia correlativa embebida en `requiere`) |
| `POST` | `/materias/` | Admin | `MateriaCreate`. `409` si el `codigo` ya existe en esa carrera |
| `PUT` | `/materias/{id}` | Admin | `MateriaUpdate` (parcial) |
| `DELETE` | `/materias/{id}` | Admin | `409` si la materia tiene cursadas |

Validaciones de catálogo (todas devuelven `422` con `errors[]`):
`anio` 1–6 · `cuatrimestre` 1 o 2 · `duracion_cuatrimestres` 1–12 ·
`nombre` ≥ 2 · `codigo` no vacío.

### 3.2 Cursadas y promedio

> ⚠️ Ver *§5 Gaps conocidos*: hoy el `usuario_id` va en la URL y **no** se valida
> contra el token. En Sprint 2 pasa a salir del token y estos paths cambian.

| Método | Path | Acceso hoy | Notas |
|--------|------|------------|-------|
| `GET` | `/materias/usuario/{usuario_id}` | Pub (hoy) | cursadas del alumno, paginado → `MateriaUsuarioResponse` |
| `POST` | `/materias/usuario/{usuario_id}` | Pub (hoy) | `MateriaUsuarioCreate`. `409` si ya está cargada o si la materia no es de la carrera del alumno |
| `PATCH` | `/materias/cursada/{materia_usuario_id}` | Pub (hoy) | `MateriaUsuarioUpdate` (parcial) |
| `DELETE` | `/materias/cursada/{materia_usuario_id}` | Pub (hoy) | `204` |
| `GET` | `/materias/promedio/{usuario_id}` | Pub (hoy) | `{ promedio: number\|null, materias_computadas: number }` |

Notas 1–10 (`422` fuera de rango). `estado` en la respuesta es derivado:
`"cursando"` si `cursando=true`, si no `"aprobada"` cuando hay `nota_final`, si no
`"pendiente"`.

### 3.3 Recursos de estudio

| Método | Path | Acceso | Notas |
|--------|------|--------|-------|
| `GET` | `/recursos/` | Pub | filtros `materia_id`, `tipo`, `desde`, `hasta` (fechas `YYYY-MM-DD`) + paginación → `RecursoResponse` |
| `GET` | `/recursos/materia/{materia_id}` | Pub | paginado |
| `GET` | `/recursos/usuario/{usuario_id}` | Pub | paginado |
| `GET` | `/recursos/{id}` | Pub | `RecursoResponse` |
| `POST` | `/recursos/` | Auth | `RecursoCreate`. El dueño sale del token → **no** mandes `usuario_id` |
| `PUT` | `/recursos/{id}` | Auth (**solo dueño**) | `403` si el recurso es de otro |
| `DELETE` | `/recursos/{id}` | Auth (**solo dueño**) | `403` si es de otro, `204` si OK |

`url` tiene que ser una URL válida (`http/https`). `titulo` 1–150.
`tipo` es libre (convención: `"pdf"`, `"video"`, `"link"`).

### 3.4 Convenios y TalentoTech

> ⚠️ Ver *§5*: la escritura **debería** ser solo admin pero hoy no está protegida.
> Tratarlos como **solo lectura** desde el front del estudiante.

| Método | Path | Acceso | Notas |
|--------|------|--------|-------|
| `GET` | `/convenios/` | Pub | paginado → `ConvenioResponse` |
| `GET` | `/convenios/carrera/{carrera_id}` | Pub | paginado |
| `GET` | `/convenios/{id}` | Pub | `ConvenioResponse` |
| `GET` | `/talentotech/` | Pub | paginado → `TalentoTechResponse` |
| `GET` | `/talentotech/carrera/{carrera_id}` | Pub | paginado |
| `GET` | `/talentotech/categoria/{categoria}` | Pub | paginado |
| `GET` | `/talentotech/{id}` | Pub | `TalentoTechResponse` |
| `POST/PUT/DELETE` | `/convenios/*`, `/talentotech/*` | (admin, aún sin enforcement) | no usar desde el front del alumno |

### 3.5 Recordatorios

> ⚠️ Ver *§5*: hoy `usuario_id` va como **query param** y no se valida contra el
> token. En Sprint 2 sale del token.

| Método | Path | Acceso hoy | Notas |
|--------|------|------------|-------|
| `GET` | `/recordatorios/?usuario_id=1` | Pub (hoy) | `usuario_id` **requerido**. Filtros `tipo`, `desde`, `hasta`, `materia_id`. Paginado → `RecordatorioResponse` (ordenado por fecha desc) |
| `POST` | `/recordatorios/?usuario_id=1` | Pub (hoy) | `RecordatorioCreate`. `usuario_id` como query. `422` si `fecha` no es futura |
| `DELETE` | `/recordatorios/{id}?usuario_id=1` | Pub (hoy) | `204` |

`fecha` es datetime ISO y **tiene que ser futura**. `tipo` libre (convención
`"parcial"`, `"tp"`, `"final"`, `"otro"`).

---

## 4. Tipos (TypeScript)

```ts
// ---- envoltorios ----
export interface Paginated<T> {
  items: T[]; total: number; page: number; per_page: number; total_pages: number;
}
export interface ApiError { detail: string; errors?: { campo: string; msg: string }[]; }

// ---- auth ----
export type Rol = "estudiante" | "admin";
export interface Usuario {
  id: number; nombre: string; email: string; carrera_id: number;
  fecha_registro: string; rol: Rol;
}
export interface LoginRequest { email: string; password: string; }
export interface RegistroRequest {
  nombre: string; email: string; password: string; carrera_id: number;
}
export interface TokenResponse {
  access_token: string; token_type: "bearer"; usuario: Usuario | null;
}

// ---- catálogo ----
export interface Carrera {
  id: number; nombre: string; duracion_cuatrimestres: number; ifts_id: number;
}
export interface Materia {
  id: number; nombre: string; codigo: string; carrera_id: number;
  anio: number; cuatrimestre: 1 | 2;
}
export interface Correlativa {
  id: number; materia_id: number; requiere_id: number; requiere: Materia | null;
}
export interface MateriaCreate {
  carrera_id: number; nombre: string; codigo: string; anio: number; cuatrimestre: 1 | 2;
}

// ---- cursadas ----
export type EstadoCursada = "cursando" | "aprobada" | "pendiente";
export interface Cursada {
  id: number; usuario_id: number; materia_id: number; cursando: boolean;
  estado: EstadoCursada;
  nota_parcial_1: number | null; nota_parcial_2: number | null; nota_final: number | null;
}
export interface CursadaCreate {
  materia_id: number; cursando?: boolean;
  nota_parcial_1?: number | null; nota_parcial_2?: number | null; nota_final?: number | null;
}
export interface Promedio { promedio: number | null; materias_computadas: number; }

// ---- recursos ----
export interface Recurso {
  id: number; usuario_id: number; fecha_creacion: string;
  titulo: string; url: string; descripcion: string; tipo: string | null; materia_id: number;
}
export interface RecursoCreate {
  titulo: string; url: string; descripcion: string; tipo?: string | null; materia_id: number;
}
export interface Convenio {
  id: number; institucion: string; carrera_destino: string; descripcion: string;
  link_info: string; carrera_id: number;
}
export interface TalentoTech {
  id: number; carrera_id: number; nombre_curso: string; categoria: string;
  descripcion: string; duracion: string; link_inscripcion: string;
}

// ---- recordatorios ----
export interface Recordatorio {
  id: number; titulo: string; fecha: string; tipo: string;
  usuario_id: number; materia_id: number | null;
}
export interface RecordatorioCreate {
  titulo: string; fecha: string; tipo: string; materia_id?: number | null;
}
```

---

## 5. Gaps conocidos (a resolver en Sprint 2 del backend)

El front tiene que asumir estos comportamientos **hoy** y estar preparado para el
cambio:

1. **Identidad no sale del token en cursadas y recordatorios.**
   Hoy el `usuario_id` viaja en la URL/query y el backend no lo valida.
   → **Encapsulá el `usuario_id` en el cliente API** (una sola función que lo
   agrega desde el `usuario` logueado). Cuando el backend lo tome del token,
   cambiás solo esa función y las URLs, no cada pantalla.

2. **`/convenios` y `/talentotech` escritura sin protección de rol.**
   El front del estudiante los trata como **solo lectura**.

3. **No hay `GET /materias/{id}` ni `GET /materias/carreras/{id}`** (detalle
   individual). Para una vista de detalle: traer de la lista y cachear, o esperar
   los endpoints (Sprint 2, Integrante 4 del back).

4. **CORS**: si el front no corre en `:5173`, pedir que agreguen el origin.

---

## 6. Recomendaciones de implementación

- **Cliente generado**: `npx openapi-typescript http://localhost:8000/openapi.json
  -o src/api/schema.d.ts` para tipos; o `orval`/`openapi-generator` para cliente +
  hooks. Regenerar cuando cambie el backend.
- **Data fetching**: TanStack Query. Key por endpoint + params; invalidar en
  mutations (ej. crear cursada → invalidar `["cursadas", userId]` y
  `["promedio", userId]`).
- **Wrapper HTTP** único con: base URL, header `Authorization`, parseo de error a
  `ApiError`, side-effect en `401`.
- **Formularios**: al recibir `422`, recorrer `errors[]` y setear el error por
  `campo`. Para el resto de los códigos, toast con `detail`.
- **Ownership**: en recursos, comparar `recurso.usuario_id === usuario.id` para
  mostrar/ocultar Editar/Borrar; igual manejar el `403` por si acaso.
- **Paginación**: componente reutilizable que recibe `Paginated<T>` y setea
  `page`.
- **`.env`**: `VITE_API_URL=http://localhost:8000`.
