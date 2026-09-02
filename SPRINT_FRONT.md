# Sprint Front de 4 días - miIFTS
**Objetivo:** Front funcional del MVP contra la API existente — auth, catálogo,
mis cursadas + promedio, recordatorios y recursos, siguiendo el contrato de
`docs/INTEGRACION_FRONT.md`.

> **Stack asumido:** Vite + React + TypeScript + React Router + TanStack Query.
> Cambiable, pero las tareas y los entregables asumen esto.
>
> **Leer primero:** `docs/INTEGRACION_FRONT.md` (contrato de respuestas,
> auth, referencia de endpoints, tipos TS, *gaps conocidos*).
>
> **Base URL dev:** `http://localhost:8000` en `VITE_API_URL`. El backend ya
> acepta CORS desde `http://localhost:5173`.

---

## 📊 Distribución de Tareas por Integrante

### 🧱 **Integrante 1 - FUNDACIONES: setup, cliente API y auth**
**Prioridad:** ALTA | **Complejidad:** Media | **Días:** 3-4
**Es la base del resto — lo del día 1-2 desbloquea a los otros 3.**

#### Tareas:
1. **Scaffolding**
   - `npm create vite@latest` (React + TS), React Router, TanStack Query,
     ESLint + Prettier. Estructura: `src/api/`, `src/auth/`, `src/features/`,
     `src/components/`, `src/pages/`.
   - `.env` → `VITE_API_URL=http://localhost:8000`.

2. **Tipos compartidos**
   - Generar tipos desde el OpenAPI:
     `npx openapi-typescript $VITE_API_URL/openapi.json -o src/api/schema.d.ts`.
   - O tipear a mano desde `docs/INTEGRACION_FRONT.md` §4. Dejar un `src/api/types.ts`
     con `Paginated<T>`, `ApiError`, `Usuario`, etc.

3. **Wrapper HTTP** (`src/api/client.ts`)
   - Una función `request(path, { method, body, auth })` con: base URL, header
     `Authorization: Bearer` cuando `auth`, `Content-Type: application/json`.
   - Parseo de error → `ApiError` (`{ detail, errors? }`). En `204` no parsear body.
   - Side-effect global: al recibir `401` → `logout()` + redirect a `/login`.

4. **Auth** (`src/auth/`)
   - Context/store con `usuario: Usuario | null` y `token: string | null`,
     persistidos en `localStorage`.
   - `login(email, pass)` → `POST /auth/login`, guarda `access_token` + `usuario`.
   - `register(payload)` → `POST /auth/registro`, luego auto-login.
   - `logout()` → limpia storage + redirige.
   - `<RutaProtegida>`: si no hay token, redirige a `/login`.

5. **Helper de identidad** (`src/api/scope.ts`)
   - `withUsuarioId(params?)` → agrega `usuario_id` del `usuario` logueado.
     **Todas** las llamadas a cursadas y recordatorios pasan por acá
     (ver *gap #1* del doc: cuando el backend tome la identidad del token, se
     cambia solo esta función).

6. **Layout + páginas de auth**
   - `Login`, `Registro` (con `<select>` de carreras vía `GET /materias/carreras`,
     público).
   - Navbar: nombre del usuario, logout, y link al ABM de catálogo **solo si**
     `usuario.rol === "admin"`.

**Entregables:**
- [ ] `npm run dev` levanta; login / registro / logout funcionando
- [ ] `<RutaProtegida>` redirige sin token; un `401` de la API desloguea
- [ ] `client.ts`, `types.ts` y `withUsuarioId()` documentados y usados por el resto
- [ ] README del front: cómo correr, variables de entorno, cómo regenerar tipos

---

### 📚 **Integrante 2 - CATÁLOGO ACADÉMICO (lectura pública)**
**Prioridad:** ALTA | **Complejidad:** Media | **Días:** 3

#### Tareas:
1. **Componente `<Paginador>`** reutilizable
   - Recibe `Paginated<T>` + `onPageChange`. Muestra `page / total_pages` y
     controles. Lo usan también Int. 3 y 4.

2. **Carreras**
   - `GET /materias/carreras` (paginado) → listado. Card por carrera con
     nombre y duración.

3. **Materias por carrera**
   - Al entrar a una carrera: `GET /materias/carrera/{id}` (paginado).
   - Filtro por `anio` y `cuatrimestre` (por query a `/buscar` o filtrando en
     cliente; documentar la decisión).

4. **Búsqueda de materias**
   - `GET /materias/buscar?q=` con `anio` / `cuatrimestre` opcionales.
   - Estados: input vacío (no dispara), sin resultados (`items: []`).

5. **Correlativas**
   - `GET /materias/correlativas/{materia_id}` → mostrar cada correlativa con
     `requiere.codigo` + `requiere.nombre` (viene **embebida**, sin llamadas
     extra).

6. **(Si hay tiempo / rol admin) ABM de catálogo**
   - Forms de alta/edición de carrera y materia (`POST/PUT/DELETE`), manejando
     `422` (`errors[]` por campo) y `409` (código duplicado / borrar con
     dependencias) con el kit de UX de Int. 4.

**Entregables:**
- [ ] Navegación carreras → materias de la carrera → correlativas
- [ ] Buscador de materias con filtros y estados vacío/sin-resultados
- [ ] `<Paginador>` reutilizable publicado para el equipo
- [ ] Estados de carga / error / vacío en todas las vistas

---

### 🎓 **Integrante 3 - MI CARRERA: cursadas, promedio y recordatorios**
**Prioridad:** ALTA | **Complejidad:** Media-Alta | **Días:** 4

> Todas las llamadas van por `withUsuarioId()` de Int. 1.

#### Tareas:
1. **Mis cursadas**
   - `GET /materias/usuario/{usuario_id}` (paginado) → tabla con `estado`
     (`cursando` / `aprobada` / `pendiente`), notas parciales y final.

2. **Alta de cursada**
   - Form: `materia_id` (select de materias **de mi carrera** —
     `usuario.carrera_id` → `GET /materias/carrera/{id}`), `cursando`, notas.
   - Manejar `409` ("ya está cargada" / "no pertenece a la carrera del alumno")
     y `422` (nota fuera de 1–10).

3. **Editar / borrar cursada**
   - `PATCH /materias/cursada/{id}` (parcial), `DELETE` (`204`).

4. **Promedio**
   - `GET /materias/promedio/{usuario_id}` → card con `promedio` y
     `materias_computadas`; contemplar `promedio: null` (“sin notas finales”).
   - Invalidar esta query cuando se crea/edita/borra una cursada.

5. **Agenda de recordatorios**
   - `GET /recordatorios/?usuario_id=` con filtros `tipo`, `desde`, `hasta`,
     `materia_id` (viene ordenado por fecha desc).
   - Alta (`POST`): `titulo`, `fecha` (datetime, **futura**), `tipo`
     (`parcial`/`tp`/`final`/`otro`), `materia_id?`. Si `422` → mostrar el error
     de `fecha` en el form.
   - Borrar (`DELETE`, `204`).

**Entregables:**
- [ ] CRUD de cursadas con manejo de `409` / `422`
- [ ] Card de promedio que reacciona a cambios en cursadas
- [ ] Agenda de recordatorios con filtros + alta con validación de fecha futura
- [ ] Todo scoped al usuario logueado vía `withUsuarioId()` (sin `usuario_id` hardcodeado en pantallas)

---

### 🔗 **Integrante 4 - RECURSOS + UX TRANSVERSAL**
**Prioridad:** MEDIA | **Complejidad:** Media | **Días:** 3
**El kit de UX del punto 4 lo necesitan los otros 3 → sacarlo día 1-2.**

#### Tareas:
1. **Recursos: listado y filtros**
   - `GET /recursos/` con filtros `materia_id`, `tipo`, `desde`, `hasta`
     (`YYYY-MM-DD`) + paginación.

2. **Alta de recurso**
   - `POST /recursos/` (requiere login). Form: `titulo` (1–150), `url`
     (validar http/https en cliente), `descripcion`, `tipo?`, `materia_id`.
     **No** mandar `usuario_id` (sale del token). Manejar `422`.

3. **Editar / borrar recurso (solo dueño)**
   - Mostrar acciones solo si `recurso.usuario_id === usuario.id`.
   - `PUT` / `DELETE /recursos/{id}`; manejar `403` igual (por las dudas).

4. **Kit de UX transversal** (`src/components/`)
   - `<Toaster>` + `useToast()` que muestra `error.detail`.
   - `useApiForm()`: al recibir `ApiError` con `errors[]`, mapea `campo → mensaje`
     y expone `fieldErrors`.
   - `<Cargando>`, `<Vacio>`, `<ErrorState onReintentar>`, skeletons.

5. **Convenios y TalentoTech (solo lectura)**
   - `GET /convenios/` y `/convenios/carrera/{id}`; `GET /talentotech/`,
     `/talentotech/carrera/{id}`, `/talentotech/categoria/{cat}`.
   - Listados con `<Paginador>`. Link externo a `link_info` / `link_inscripcion`.

**Entregables:**
- [ ] Módulo de recursos con filtros, alta y edición/borrado solo del dueño
- [ ] Kit de UX (`toasts`, `useApiForm`, estados de carga/vacío/error) publicado día 2
- [ ] Vistas de convenios y TalentoTech (solo lectura)

---

## 📅 Cronograma sugerido

### **Día 1**
- Int. 1: scaffolding + `client.ts` + tipos + esqueleto de auth.
- Int. 2: `<Paginador>` + lista de carreras.
- Int. 3: lista de "mis cursadas" (mockeando identidad si hace falta).
- Int. 4: kit de UX (toasts, estados, `useApiForm`).

### **Día 2**
- Int. 1: login / registro / `<RutaProtegida>` / `withUsuarioId()` + layout.
- Int. 2: materias por carrera + filtros.
- Int. 3: alta/edición de cursada + manejo de `409`/`422`.
- Int. 4: recursos — listado + filtros.

### **Día 3**
- Int. 1: navbar por rol + pulido de sesión (expiración, refresh de `usuario`).
- Int. 2: búsqueda de materias + correlativas embebidas.
- Int. 3: promedio + invalidación de queries.
- Int. 4: alta de recurso + ownership en editar/borrar.

### **Día 4**
- Int. 3: agenda de recordatorios (filtros + alta con fecha futura).
- Int. 2: (si hay admin) ABM de catálogo.
- Int. 4: convenios + TalentoTech.
- Todos: prueba de punta a punta contra el backend, README del front, PRs.

---

## ✅ Criterios de aceptación

1. **Auth:**
   - [ ] Registro (con select de carreras), login y logout funcionando.
   - [ ] Rutas privadas redirigen sin token; un `401` desloguea.

2. **Funcionalidad MVP:**
   - [ ] Se navega el catálogo (carreras → materias → correlativas) y se busca.
   - [ ] El alumno ve/crea/edita/borra sus cursadas y ve su promedio.
   - [ ] El alumno gestiona sus recordatorios con filtros y fecha futura.
   - [ ] El alumno lista recursos con filtros y crea/edita/borra los propios.

3. **Contrato:**
   - [ ] Toda lista usa `{items,total,...}` y el `<Paginador>` común.
   - [ ] Errores: `detail` en toast; `errors[]` mapeado a campos en los forms.
   - [ ] `usuario_id` sale siempre de `withUsuarioId()`, nunca hardcodeado en vistas.

4. **Proceso:**
   - [ ] Cada feature en su rama; PRs revisados por ≥1 compañero.
   - [ ] README del front: correr, `.env`, regenerar tipos.

---

## 🚀 Bonus (si sobra tiempo)

1. **Dark mode** / tema.
2. **Optimistic updates** en cursadas y recordatorios.
3. **Cliente 100% generado** (`orval`) con hooks de React Query.
4. **Tests** con Vitest + Testing Library de los flujos de auth y de un form con `errors[]`.
5. **Deploy del front** (Vercel / Netlify / Pages) apuntando al backend desplegado.
6. **Manejo de expiración**: avisar al usuario ~1 min antes de que venza el token.

---

## 📞 Coordinación

### Daily Standup (10 min)
- ¿Qué hice ayer? ¿Qué haré hoy? ¿Tengo algún blocker?

### Dependencias críticas
- **Int. 1** entrega `client.ts` + `types.ts` + `withUsuarioId()` + auth **día 1-2**.
- **Int. 2** entrega `<Paginador>` **día 1**.
- **Int. 4** entrega el kit de UX (`useApiForm`, toasts, estados) **día 2**.
- Int. 3 puede arrancar con datos mockeados y enchufar la API cuando 1 y 4 estén.

### Git Flow (repo del front)
```bash
git checkout main
git pull origin main
git checkout -b feature/tu-nombre-tarea

git add .
git commit -m "feat: descripción clara"
git push origin feature/tu-nombre-tarea
# PR: feature/tu-nombre → main (o dev), review de ≥1 compañero
```

---

## 🎯 Métricas de éxito

- Pantallas del MVP funcionando de punta a punta contra el backend: objetivo 100%.
- Endpoints del contrato consumidos: objetivo 100% de los `GET`/escrituras del MVP.
- Formularios que mapean `errors[]` a campos: objetivo 100%.
- Componentes transversales reutilizados (`<Paginador>`, kit de UX): en todas las features.
- PRs mergeados con review: objetivo 100%.
