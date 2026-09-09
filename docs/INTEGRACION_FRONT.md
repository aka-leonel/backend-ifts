# Integración Front ↔ Backend miIFTS

Documento único para el equipo de front: **contexto del proyecto**, **contrato de la API**
y **arquitectura del frontend** (pantallas, componentes, stack, tareas).

> Fuente de verdad viva: `GET /openapi.json` y Swagger en `/docs`.
> Copia versionada del contrato: `docs/openapi.json` (regenerar con
> `python scripts/export_openapi.py` cuando cambie la API).

---

# PARTE 0 · Contexto del proyecto

## 0.1 Qué es

**miIFTS** es una PWA para estudiantes de los IFTS de CABA (Institutos de Formación
Técnica Superior). El alumno lleva el seguimiento de su carrera: qué materias cursa o
aprobó y con qué notas, recordatorios de parciales y finales, links de material de
estudio, e información de convenios universitarios y cursos TalentoTech. Un rol **admin**
administra el catálogo académico.

## 0.2 Stack backend

FastAPI 0.115 + SQLAlchemy 2.0 + Pydantic v2. Auth JWT HS256 (24 h). Passwords con bcrypt.
Arquitectura por capas y por feature: `router → service → repository → model`, con
`app/shared/` para paginación y jerarquía de errores. SQLite en local y tests,
PostgreSQL gestionado en la nube.

## 0.3 Modelo de datos

```
IFTS
 └─ Carrera (ifts_id)
     ├─ Materia (carrera_id · codigo único por carrera, ej "1.1.3")
     │   └─ Correlativa (materia_id → requiere_id)
     └─ Usuario (carrera_id · rol)
         ├─ MateriaUsuario  → "cursada": cursando + notas parciales + final
         ├─ Recordatorio    → fecha futura + tipo
         └─ Recurso         → link de material + tipo
Convenio (carrera_id) · TalentoTech (carrera_id)   ← catálogo, solo lectura para el alumno
```

## 0.4 Estado del backend (Sprint 2, al 2026-09-08)

En `dev`: identidad desde el token en cursadas y recordatorios (PR #11 / #12), roles +
pins en convenios/talentotech (#13), endpoints de detalle + `openapi.json` + este doc (#14).
Suite: 90 tests. Pendiente de infra (no cambia el contrato): Postgres gestionado, Alembic,
deploy, CI bloqueante. **Gaps que sí tocan al front:** ver §1.7.

## 0.5 Roles

| Rol | Qué puede |
|-----|-----------|
| `estudiante` | default. Gestiona lo suyo: cursadas, recordatorios, recursos propios. |
| `admin` | además, ABM del catálogo (carreras, materias, convenios, TalentoTech). |

El backend autoriza (`403`). El front solo muestra u oculta UI según `usuario.rol`.

---

# PARTE 1 · Contrato de la API

## 1.1 Configuración

| Item | Valor |
|------|-------|
| Base URL dev | `http://localhost:8000` — configurable con `VITE_API_URL` |
| CORS | `http://localhost:5173`, `http://127.0.0.1:5173`. Otro origen → pedir a backend agregarlo a `CORS_ORIGINS` |
| Formato | JSON. Fechas ISO 8601 |

## 1.2 Shapes de respuesta

| Caso | Forma |
|------|-------|
| **Colección** (todo `GET` de lista) | `{ items: T[], total, page, per_page, total_pages }` |
| **Recurso** (`GET`/`POST`/`PUT`/`PATCH` de un ítem) | objeto plano `T` |
| **DELETE** | `204` sin body |
| **Error** | `{ detail: string }` |
| **Validación `422`** | `{ detail: string, errors: { campo: string, msg: string }[] }` |

`detail` es **siempre** un string → mostrarlo tal cual en un toast.
`errors[].campo` es el nombre del field (con punto si es anidado, ej. `"requiere.codigo"`)
→ marcar ese input en el formulario.

## 1.3 Paginación

Todos los listados aceptan `?page=1&per_page=20` (`per_page` rango 1–100). Página fuera de
rango → `items: []` con el `total` real. `total_pages` dice cuántas hay.

## 1.4 Códigos HTTP

`200` OK · `201` creado · `204` borrado (no parsear body) · `401` token ausente/inválido
→ limpiar sesión + ir a login · `403` sin permiso · `404` no existe · `409` duplicado o
regla de negocio · `422` validación (pintar `errors[]` en el form).

## 1.5 Autenticación (JWT)

HS256, expira a las **24 h**. No hay refresh token ni logout de servidor → "cerrar sesión"
= borrar el token del cliente. Header `Authorization: Bearer <access_token>` en cada request
autenticado. Interceptor: `401` → borrar token + `usuario` → `/login`.

| Método | Path | Auth | Request → Response |
|--------|------|------|-------------------|
| `POST` | `/auth/registro` | Pub | `{ nombre, email, password, carrera_id }` → `201` `UsuarioResponse` (**sin token**) |
| `POST` | `/auth/login` | Pub | `{ email, password }` → `{ access_token, token_type:"bearer", usuario }` |
| `GET` | `/auth/me` | Bearer | → `UsuarioResponse` |
| `GET` | `/auth/verify` | Bearer | → `{ valid: true, user_id }` |

Validaciones: `password` ≥ 8 con al menos una letra y un número · `nombre` 2–100 ·
`carrera_id` debe existir (traer con `GET /materias/carreras`) · `email` único ·
`rol` se ignora (siempre `estudiante`). El login ya trae `usuario` → no hace falta `/auth/me`
después.

## 1.6 Endpoints por dominio

Convención: **Pub** sin token · **Auth** Bearer · **Admin** Bearer + rol admin.

### Catálogo académico

| Método | Path | Acceso | Notas |
|--------|------|--------|-------|
| `GET` | `/materias/carreras` | Pub | paginado `Carrera` |
| `GET` | `/materias/carreras/{id}` | Pub | `Carrera` · `404` |
| `GET` | `/materias/carrera/{carrera_id}` | Pub | materias de la carrera, paginado `Materia` |
| `GET` | `/materias/buscar?q=&anio=&cuatrimestre=` | Pub | `q` requerido (nombre/código) |
| `GET` | `/materias/correlativas/{materia_id}` | Pub | paginado `Correlativa` (con `requiere: Materia` embebido) |
| `GET` | `/materias/{materia_id}` | Pub | `Materia` · `404` |
| `POST` / `PUT` / `DELETE` | `/materias/carreras/*`, `/materias/*` | Admin | ABM |

Validaciones: `anio` 1–6 · `cuatrimestre` 1 o 2 · `duracion_cuatrimestres` 1–12 ·
`nombre` ≥ 2 · `codigo` no vacío (se guarda en mayúsculas). ABM: `409` si el código está
duplicado en la carrera, si se borra una carrera con materias, o una materia con cursadas.

### Cursadas y promedio

> Identidad desde el **token**. `POST`/`PATCH`/`DELETE` **no** llevan `usuario_id`.
> En los `GET` con `{usuario_id}` un alumno solo consulta lo suyo (`403` si no); admin cualquiera.

| Método | Path | Acceso | Notas |
|--------|------|--------|-------|
| `GET` | `/materias/usuario/{usuario_id}` | Auth (propio/admin) | paginado `Cursada` |
| `POST` | `/materias/usuario` | Auth | `{ materia_id, cursando?, nota_parcial_1?, nota_parcial_2?, nota_final? }` · `409` si ya está cargada o la materia no es de tu carrera |
| `PATCH` | `/materias/cursada/{id}` | Auth (dueño) | parcial · `404` si es de otro |
| `DELETE` | `/materias/cursada/{id}` | Auth (dueño) | `204` · `404` si es de otro |
| `GET` | `/materias/promedio/{usuario_id}` | Auth (propio/admin) | `{ promedio: number\|null, materias_computadas }` |

Notas 1–10 (`422`). **`estado` es derivado**, no un campo que se manda:
`"cursando"` si `cursando=true`; si no `"aprobada"` cuando hay `nota_final`; si no `"pendiente"`.

### Recursos de estudio

| Método | Path | Acceso | Notas |
|--------|------|--------|-------|
| `GET` | `/recursos/?materia_id=&tipo=&desde=&hasta=` | Pub | filtros (`desde`/`hasta` = `YYYY-MM-DD`) + paginado |
| `GET` | `/recursos/materia/{materia_id}` | Pub | paginado |
| `GET` | `/recursos/{id}` | Pub | `Recurso` |
| `POST` | `/recursos/` | Auth | `RecursoCreate` (**sin** `usuario_id`) |
| `PUT` / `DELETE` | `/recursos/{id}` | Auth (**solo dueño**) | `403` si es de otro |

`url` HttpUrl (`http/https`) · `titulo` 1–150 · `descripcion` requerida · `tipo` libre
(convención `pdf` / `video` / `link`) · `fecha_creacion` la pone el servidor.

### Convenios y TalentoTech

Lectura pública, escritura solo admin. Desde el front del alumno son **solo lectura**.
`GET /convenios/` · `/convenios/carrera/{id}` · `/convenios/{id}` ·
`GET /talentotech/` · `/talentotech/carrera/{id}` · `/talentotech/categoria/{cat}` · `/talentotech/{id}`.

### Recordatorios

> Identidad desde el **token** — no mandar `usuario_id`. Un alumno solo ve/borra los suyos;
> borrar uno ajeno da `404` (no se revela que existe).

| Método | Path | Acceso | Notas |
|--------|------|--------|-------|
| `GET` | `/recordatorios/?tipo=&desde=&hasta=&materia_id=` | Auth | solo los del token, orden fecha desc, paginado |
| `POST` | `/recordatorios/` | Auth | `{ titulo, fecha: ISO futura, tipo, materia_id? }` · `201` · `422` si `fecha` no es futura |
| `DELETE` | `/recordatorios/{id}` | Auth (dueño) | `204` · `404` si es de otro |

`tipo` libre (convención `parcial` / `tp` / `final` / `otro`).

## 1.7 Gaps abiertos (el front los necesita, faltan en el backend)

| Falta | Para qué | Estado / workaround |
|-------|----------|---------------------|
| `PATCH /recordatorios/{id}` + schema `RecordatorioUpdate` | Botón **editar** en la card de recordatorio | **Sprint 2 · Integrante 1.** Mientras tanto el front hace `DELETE` + `POST` (cambia el `id`). |
| `PATCH /auth/me` con `{ nombre?, carrera_id? }` | Pantalla **Mi perfil**: editar nombre / cambiar carrera | **Sprint 2 · Integrante 4.** Mientras tanto los campos de perfil son solo visuales. |

## 1.8 Modelos TypeScript

**Generar desde el OpenAPI** (fuente de verdad, no tipear a mano las respuestas):

```bash
npx openapi-typescript http://localhost:8000/openapi.json -o src/api/schema.d.ts
# package.json → "scripts": { "gen:api": "openapi-typescript http://localhost:8000/openapi.json -o src/api/schema.d.ts" }
```

Alias legibles en `src/api/types.ts`:

```ts
import type { components } from './schema';
type S = components['schemas'];

export type Usuario            = S['UsuarioResponse'];
export type Carrera            = S['CarreraResponse'];
export type Materia            = S['MateriaResponse'];
export type Correlativa        = S['CorrelativaResponse'];
export type Cursada            = S['MateriaUsuarioResponse'];   // leer
export type CursadaCreate      = S['MateriaUsuarioCreate'];     // FormModal materia (POST)
export type CursadaUpdate      = S['MateriaUsuarioUpdate'];     // FormModal materia (PATCH)
export type Promedio           = S['PromedioResponse'];
export type Recordatorio       = S['RecordatorioResponse'];
export type RecordatorioCreate = S['RecordatorioCreate'];
export type Recurso            = S['RecursoResponse'];
export type RecursoCreate      = S['RecursoCreate'];
export type Token              = S['TokenResponse'];

export type Paginated<T> = { items: T[]; total: number; page: number; per_page: number; total_pages: number };
export type ApiError = { detail: string; errors?: { campo: string; msg: string }[] };
```

**Leer y escribir tienen tipos distintos.** `Cursada` (respuesta: `id`, `usuario_id`,
`materia_id`, `cursando`, `estado` derivado, `nota_parcial_1/2`, `nota_final`) ≠
`CursadaCreate` (solo `materia_id` + notas opcionales) ≠ `CursadaUpdate` (parcial).
`openapi-typescript` genera los tres.

---

# PARTE 2 · Arquitectura del front

## 2.1 Principios

1. **Cuatro arquetipos, no una pantalla por caso de uso:** Auth · Panel · Lista · Detalle.
2. **Los formularios no son pantallas:** un único `<FormModal>` + `fieldSpec` (§2.9).
3. **El estado de la materia es derivado** (§1.6), no un dropdown que se elige.
4. **Los recursos y recordatorios de una materia viven en su detalle.**
5. **La identidad sale del token:** nunca `usuario_id` en la URL de cursadas/recordatorios.
6. **Una lista = query hook + render de ítem,** dentro de `<ListScreen>`.
7. **Mobile-first:** tab bar inferior, una columna, formularios en modal/sheet.

## 2.2 Stack

Vite + React + TypeScript + React Router + TanStack Query + **Tailwind**.

- **Tailwind, no Bootstrap.** El diseño (`miIFTS_design_system.pdf`) es a medida (paleta,
  radios, espaciado propios, dark-first). Bootstrap trae componentes ya estilados que hay
  que pelear; Tailwind son utilidades sobre *tus* tokens, sin CSS que sobreescribir. El
  export de Figma Make ya viene en React + Tailwind.
- **Estado de servidor = TanStack Query.** Estado de UI (modal abierto, chip activo) =
  `useState`. Sin Redux/Zustand para este MVP.
- **shadcn/ui** opcional para `Modal` / `Select` / `Switch` accesibles (Tailwind + Radix,
  se re-estila con los tokens). No es obligatorio.

## 2.3 Tokens (de `miIFTS_design_system.pdf` a `tailwind.config.js`)

Dark mode fijo (`<html class="dark">`, sin toggle).

```
colors:  bg #111218 · card #1A1B23 · surface2 #2A2B36 · primary #8C7DFF ·
         secondary #B87EED · accent #CFFF5E · ok #3FB950 · text #E8E8F0 / #9A9AB0
radius:  card 14 · btn 10 · pill 20
font:    Inter
```

Nada de color / radio / espaciado sueltos en las pantallas: solo vía token o vía primitivo
(`<Button variant="primary">`, no `class="bg-[#8C7DFF]…"` copiado).

## 2.4 Modelo de navegación

Tab bar inferior fija, **5 destinos** (activo violeta). Onboarding sin tabs.

```
/login                 · pública
/registro              · pública
/onboarding/carrera    · elegí tu carrera (GET /materias/carreras)
AppShell (RutaProtegida + BottomTabs)
├─ /                 · Inicio         (Panel)
├─ /materias         · Materias       (Lista · Byte/PromedioCard arriba · FAB +)
│   └─ /materias/:id · Detalle materia (correlativas + Recursos + Recordatorios de la materia)
├─ /recordatorios    · Agenda global  (Lista · agrupada por semana)
├─ /convenios        · Convenios      (Lista con Tabs Universidades / TalentoTech · solo lectura)
└─ /perfil           · Mi perfil      (Panel · editar nombre / carrera · cerrar sesión)
/admin/catalogo      · opcional · solo admin
```

`Recursos` **dejó de ser pantalla propia**: se accede desde el detalle de la materia.

## 2.5 Arquetipos de pantalla

| | Arquetipo | Lo usan | Anatomía |
|-|-----------|---------|----------|
| **A** | Auth | Login, Registro, Elegí carrera | AuthLayout › logo › Form(Field…) › Button primary › switch link |
| **B** | Panel | Inicio, Perfil | AppHeader › Card × N › (acciones) |
| **C** | Lista | Materias, Recordatorios, Convenios | AppHeader (+ acción) › FilterChips › ListState(Skeleton/Empty/Error/items) |
| **D** | Detalle | Materia | DetailScreen › meta(chips, notas) › Section(correlativas) › Section(recursos + FormModal) › Section(recordatorios + FormModal) |

## 2.6 Inventario de pantallas

| Ruta | Arquetipo | Qué es |
|------|-----------|--------|
| `/login` | A | email + contraseña |
| `/registro` | A | nombre + email + contraseña → sigue a elegí carrera |
| `/onboarding/carrera` | C | carreras listadas; al elegir → `POST /auth/registro` + auto-login |
| `/` | B | Byte con progreso, próximos recordatorios (solo lectura), accesos |
| `/materias` | C | cards de materia con badge y nota · chips de filtro · FAB + → FormModal |
| `/materias/:id` | D | badge + notas + "editar notas"; **Sección Recursos** (cards con editar + "agregar recurso"); **Sección Recordatorios** de la materia (cards con editar + "agregar recordatorio") |
| `/recordatorios` | C | agenda global agrupada por semana · dot por tipo · swipe para borrar · FAB + |
| `/convenios` | C | Tabs Universidades / TalentoTech · cards con "más info" |
| `/perfil` | B | nombre editable · carrera (select) · guardar · progreso · cerrar sesión |
| `/admin/catalogo` | C | **opcional** · solo admin · ABM carreras/materias |

`*` (404), `403` y offline **no** son rutas: se renderizan como estado dentro de la pantalla
que falló.

## 2.7 Librería de componentes

Lista **cerrada**. Nada se dibuja fuera de acá sin agregarlo primero. Los frames de Figma se
nombran 1:1 con estos.

**Tier 0 · primitivos** (salen de los tokens de §2.3):
`Button` (primary/secondary/ghost/danger) · `Field` (label + control + error) · `TextInput` ·
`Select` · `NumberInput` (1–10) · `DateTimeField` · `Switch` · `Chip` · `Card` · `Modal` ·
`Sheet` · `Tabs` · `Toaster` · `Skeleton` · `IconButton`.

**Tier 1 · shell:**
`AppShell` (AppHeader + Outlet + BottomTabs) · `AuthLayout` · `BottomTabs` (5) · `AppHeader` ·
`RutaProtegida` · `AdminOnly`.

**Tier 2 · patrones de datos** (los que evitan pantallas):
`ListScreen` · `ListState` (loading/error/vacío/ok) · `FormModal` (§2.9) · `EntityForm` ·
`ConfirmDialog` · `DetailScreen` · `Section` (con slot de acción) · `EmptyState` ·
`ErrorState` · `Paginador`.

**Tier 3 · entidades** (presentacionales, sin fetch):
`ByteWidget` (`{ aprobadas, total }` → 1 de 4 estados: Dormido/Despierto/Entusiasta/Graduado) ·
`PromedioCard` · `MateriaCard` · `CarreraCard` · `CorrelativaItem` ·
`RecursoCard` (editar/borrar si `recurso.usuario_id === usuario.id`) ·
`RecordatorioCard` (en la materia: editar/borrar; en Inicio: solo lectura) · `PerfilHeader`.

## 2.8 Infraestructura y hooks (los entrega Integrante 1)

- **`apiClient(path, { method, body, auth })`** — base `VITE_API_URL`; agrega
  `Authorization: Bearer` si `auth`; parsea todo error a `ApiError`; no lee body en `204`;
  efecto global `401 → logout() + /login`.
- **`AuthProvider` / `useAuth()`** — `{ usuario, token, login, register, logout }` en
  `localStorage`. `login` guarda `access_token` + `usuario`. `register` recibe también
  `carrera_id` (del onboarding).
- **`useApiForm()`** — de `ApiError.errors[]` arma `fieldErrors`; el resto de códigos →
  toast con `detail`.
- **`useToast()`**.

**Capas por feature** (igual que el back `repository → service → router`):

```
src/features/<x>/
  service.ts   funciones puras tipadas, 1 por endpoint (sin React): getMisMaterias(), createCursada()...
  hooks.ts     TanStack Query encima de service.ts: useMisMaterias(), useCrearCursada()...
  *.tsx        componentes — usan hooks, nunca service.ts ni apiClient directo
```

Los `fieldSpec` (§2.9) llaman a funciones de `service.ts` (`submit.create/update`), no a
`apiClient`. Los tipos de dominio ya están generados (§1.8); cada feature agrega solo sus
tipos chicos de vista/formulario. Keys e invalidación de los hooks en §2.10.

> **No armar URLs con `usuario_id`.** Para "lo mío" alcanza el header `Authorization`.
> `GET /materias/usuario/{miId}` y `/materias/promedio/{miId}` usan `usuario.id` del login
> solo porque el path lo pide; pedir el de otro → `403`.

## 2.9 El pop-up: un solo `<FormModal>`

El modal que abre el FAB `+` y el que abre el botón **editar** de una card **son el mismo
componente**. Cambia solo el `fieldSpec`: qué campos muestra, qué valida, qué endpoint pega.
Si mañana hay otro formulario, es un `fieldSpec` nuevo, no un modal nuevo.

```ts
// specs/materiaUsuario.ts — FAB + de /materias y "editar notas" del detalle
export const materiaUsuarioSpec = {
  titulo: (m) => (m ? 'Editar materia' : 'Agregar materia'),
  fields: [
    { name: 'materia_id', label: 'Materia', type: 'select', options: materiasDeMiCarrera, required: true, lockOnEdit: true },
    { name: 'cursando', label: '¿La estás cursando?', type: 'switch' },
    { name: 'nota_parcial_1', label: '1er parcial', type: 'number', min: 1, max: 10 },
    { name: 'nota_parcial_2', label: '2do parcial', type: 'number', min: 1, max: 10 },
    { name: 'nota_final', label: 'Final', type: 'number', min: 1, max: 10 },
  ],
  submit: {
    create: (v) => api.post('/materias/usuario', v),          // 201
    update: (id, v) => api.patch(`/materias/cursada/${id}`, v), // 200, parcial
  },
  onError: { 409: 'toast', 422: 'fields' },
  invalidates: (uid) => [['mis-materias', uid], ['promedio', uid]],
};

// specs/recurso.ts — "agregar recurso" y "editar" de una RecursoCard
export const recursoSpec = (materiaId) => ({
  titulo: (r) => (r ? 'Editar recurso' : 'Agregar recurso'),
  fields: [
    { name: 'titulo', label: 'Título', type: 'text', required: true, max: 150 },
    { name: 'url', label: 'Link', type: 'url', required: true },
    { name: 'descripcion', label: 'Descripción', type: 'text', required: true },
    { name: 'tipo', label: 'Tipo', type: 'select', options: ['pdf', 'video', 'link'] },
  ],
  submit: {
    create: (v) => api.post('/recursos/', { ...v, materia_id: materiaId }),
    update: (id, v) => api.put(`/recursos/${id}`, { ...v, materia_id: materiaId }),
  },
  onError: { 403: 'toast', 422: 'fields' },
  invalidates: () => [['recursos-materia', materiaId]],
});

// specs/recordatorio.ts — "agregar recordatorio" y "editar" de una RecordatorioCard
export const recordatorioSpec = (materiaId) => ({
  titulo: (r) => (r ? 'Editar recordatorio' : 'Nuevo recordatorio'),
  fields: [
    { name: 'titulo', label: 'Título', type: 'text', required: true, max: 150 },
    { name: 'fecha', label: 'Fecha y hora', type: 'datetime', required: true, rule: 'futura' },
    { name: 'tipo', label: 'Tipo', type: 'select', options: ['parcial', 'tp', 'final', 'otro'], required: true },
  ],
  submit: {
    create: (v) => api.post('/recordatorios/', { ...v, materia_id: materiaId }),
    // no hay PATCH todavía (§1.7) → borrar + recrear
    update: (id, v) => api.del(`/recordatorios/${id}`).then(() => api.post('/recordatorios/', { ...v, materia_id: materiaId })),
  },
  onError: { 422: 'fields' },
  invalidates: () => [['recordatorios']],
});
```

Al éxito `FormModal` cierra, muestra toast e invalida las queries de `invalidates`.
En `422` mapea `errors[]` → campos (`onError: 'fields'`); en `409`/`403` → toast (`'toast'`).

## 2.10 Datos: query keys e invalidación

```
['carreras', { page }]                 // onboarding
['mis-materias', usuarioId, { page }]
['promedio', usuarioId]
['materia', id]
['materias-carrera', carreraId]        // select del FormModal de materia
['correlativas', materiaId]
['recursos-materia', materiaId]
['recordatorios', filtros]             // sin filtro = agenda global; con materia_id = los de esa materia
['convenios', { page }] · ['talentotech', { page }]
['auth-me']
```

Invalidar tras mutación: materia → `['mis-materias', uid]` + `['promedio', uid]` ·
recurso → `['recursos-materia', materiaId]` · recordatorio → `['recordatorios']` ·
perfil → `['auth-me']`.

## 2.11 Pantalla → endpoints

| Pantalla | Endpoints |
|----------|-----------|
| `/login` | `POST /auth/login` |
| `/registro` | — (junta nombre / email / password) |
| `/onboarding/carrera` | `GET /materias/carreras` · `POST /auth/registro` · `POST /auth/login` |
| `/` | `GET /materias/promedio/{miId}` · `GET /materias/usuario/{miId}` · `GET /recordatorios/?desde=hoy` |
| `/materias` | `GET /materias/usuario/{miId}` · `GET /materias/promedio/{miId}` · `GET /materias/carrera/{miCarrera}` · `POST /materias/usuario` |
| `/materias/:id` | `GET /materias/{id}` · `GET /materias/correlativas/{id}` · `GET /recursos/materia/{id}` · `GET /recordatorios/?materia_id={id}` · `PATCH`·`DELETE /materias/cursada/{id}` · `POST`·`PUT`·`DELETE /recursos/{id}` · `POST`·`DELETE /recordatorios/{id}` |
| `/recordatorios` | `GET /recordatorios/?…` · `POST /recordatorios/` · `DELETE /recordatorios/{id}` |
| `/convenios` | `GET /convenios/…` · `GET /talentotech/…` |
| `/perfil` | `GET /auth/me` · `PATCH /auth/me` *(pendiente, §1.7)* |
| `/admin/catalogo` | `POST`·`PUT`·`DELETE /materias/carreras` · `POST`·`PUT`·`DELETE /materias/` |

Sin usar en este MVP: `/materias/buscar`, `/recursos/usuario/{id}`.

## 2.12 Estados transversales (ninguno es una pantalla)

| Estado | Dónde se resuelve | UI |
|--------|-------------------|-----|
| Cargando | ListState / DetailScreen | `<Skeleton>` con la forma del contenido |
| Vacío | ListState | `<EmptyState>` con acción ("Todavía no cargaste materias — Agregar") |
| Red / 5xx | ListState / DetailScreen | `<ErrorState onRetry>` |
| `401` | apiClient (global) | limpia sesión → `/login` |
| `403` | por request | `<EmptyState>` "No tenés permiso" |
| `404` | por request | `<EmptyState>` "No encontramos esto" |
| `409` | FormModal | toast con `detail` |
| `422` | useApiForm | `errors[]` → `fieldErrors` (nunca pantalla ni toast) |
| Offline (PWA) | AppShell | banner + cache de TanStack Query |

## 2.13 Del mock de Figma al código

1. El export de **Figma Make** es un **cascarón visual**: arrays hardcodeados, tipos
   inventados, sin API, sin routing, sin auth. Se conserva el JSX/CSS; el resto se tira.
2. Scaffold nuevo con Vite y la estructura de §2.7–§2.8; se pegan adentro los componentes
   visuales de Figma.
3. Por pantalla: `const materias = [...]` → `const { data } = useMisMaterias()`. Tipar cada
   componente con el modelo real (`{ materia: Cursada }`, no `{ nombre, nota }`).
4. Campos que Figma inventó y no existen (ej. los 4 estados de materia) → derivarlos en el
   front:
   ```ts
   export function estadoLabel(c: Cursada) {
     if (c.cursando) return 'En curso';
     if (c.nota_final != null) return 'Aprobada';
     if (c.nota_parcial_1 != null || c.nota_parcial_2 != null) return 'Regular';
     return 'Pendiente';
   }
   ```
5. Los pop-ups de Figma (frames/overlays) **no son rutas**: son `<FormModal>` con `useState`.
   Su layout se copia **una vez** dentro de `<EntityForm>`.
6. Después del primer import, el **código es la fuente de verdad**; no se sigue sincronizando
   con Figma.
7. Cuando el backend cambia el contrato: `python scripts/export_openapi.py` → commit de
   `docs/openapi.json` → front `npm run gen:api` → el compilador de TS marca cada lugar que
   se rompió.

## 2.14 Reparto de tareas (front · 4 integrantes)

| Quién | Entrega | Bloquea a |
|-------|---------|-----------|
| **Int. 1 — Fundaciones** | Vite + Tailwind con tokens · `apiClient` · `useAuth` · `RutaProtegida` · `AppShell` + `BottomTabs` (5) · pantallas Login / Registro / Elegí carrera | todos (día 1–2) |
| **Int. 2 — Materias** | `/materias` (lista + chips + `MateriaCard`) · `ByteWidget` / `PromedioCard` · **`FormModal` + `EntityForm` genéricos** + `materiaUsuarioSpec` | Int. 3 (FormModal, día 2) |
| **Int. 3 — Detalle de materia** | `/materias/:id` (meta + correlativas + Sección Recursos + Sección Recordatorios) · `RecursoCard` / `RecordatorioCard` con editar · `recursoSpec` + `recordatorioSpec`. Coordina el `PATCH /recordatorios/{id}` con backend | — |
| **Int. 4 — Inicio + Agenda + Convenios + Perfil + kit UX** | `/`, `/recordatorios` (agenda global), `/convenios`, `/perfil` · kit: `Toaster` / `useToast`, `useApiForm`, `EmptyState` / `ErrorState` / `Skeleton`, `ConfirmDialog` | Int. 2 y 3 (kit, día 2) |

Cada uno en `feature/<nombre>`, PR a `main` con 1 review. Cada dev levanta el backend local
(SQLite + `python seed.py`, `VITE_API_URL=http://localhost:8000`).

---

## Anexo · ejemplos de payload

```jsonc
// POST /auth/registro
{ "nombre": "Martina Ríos", "email": "martina@ifts.edu.ar", "password": "secreta123", "carrera_id": 1 }

// POST /auth/login  → 200
{ "access_token": "eyJ...", "token_type": "bearer",
  "usuario": { "id": 1, "nombre": "Martina Ríos", "email": "martina@ifts.edu.ar",
               "carrera_id": 1, "fecha_registro": "2026-09-08T12:00:00", "rol": "estudiante" } }

// POST /materias/usuario  (sin usuario_id)
{ "materia_id": 12, "cursando": true, "nota_parcial_1": 7 }

// POST /recordatorios/  (sin usuario_id, fecha futura)
{ "titulo": "Parcial 1er llamado", "fecha": "2026-10-05T18:00:00", "tipo": "parcial", "materia_id": 12 }

// error 422
{ "detail": "El cuatrimestre debe ser 1 o 2",
  "errors": [ { "campo": "cuatrimestre", "msg": "El cuatrimestre debe ser 1 o 2" } ] }
```
