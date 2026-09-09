# Sprint Front - miIFTS

**Objetivo:** front funcional del MVP contra la API existente, siguiendo
`docs/INTEGRACION_FRONT.md` (contexto del proyecto + contrato de la API + arquitectura del
front: arquetipos, componentes, `<FormModal>`, tokens de Tailwind, del mock de Figma al código).

> **Stack:** Vite + React + TypeScript + React Router + TanStack Query + **Tailwind** (dark fijo).
> **Base URL dev:** `VITE_API_URL=http://localhost:8000`. CORS ya acepta `:5173`.
> **Modelos:** `npm run gen:api` (`openapi-typescript`). No tipear las respuestas a mano.
> **Un solo pop-up:** todo formulario es `<FormModal>` + `fieldSpec` (`docs/INTEGRACION_FRONT.md` §2.9).

### Capas (igual que el back: repository → service → router)

```
src/api/          apiClient (fetch + Authorization + parseo ApiError + 401)   ← ya hecho
src/api/types.ts  alias de dominio sobre schema.d.ts generado                 ← ya hecho
src/features/<x>/
  service.ts      funciones puras tipadas, 1 por endpoint (sin React): getMisMaterias(), createCursada()...
  hooks.ts        TanStack Query encima de service.ts: useMisMaterias(), useCrearCursada()...
  <Componentes>.tsx
```

Reglas: los componentes usan **hooks**, no `service.ts` ni `apiClient` directo.
Los `fieldSpec` (`submit.create/update`) llaman a funciones de `service.ts`.
Cada integrante escribe el `service.ts` + `hooks.ts` de **sus** features, más los tipos
chicos de vista/formulario que necesite (los de dominio ya están generados).

---

## ✅ Ya entregado (Fundaciones — no rehacer)

- `src/api/`: `schema.d.ts` generado, `types.ts` con alias, `client.ts` (`apiClient` +
  `Authorization` + parseo `ApiError` + efecto global `401 → logout`).
- `src/auth/`: `AuthProvider` / `useAuth` (`{ usuario, token, login, register, logout }`
  en `localStorage`), `<RutaProtegida>`.
- Tailwind con los **tokens del design system** (`bg #111218`, `card #1A1B23`,
  `surface2 #2A2B36`, `primary #8C7DFF`, `secondary #B87EED`, `accent #CFFF5E`,
  `ok #3FB950`, texto `#E8E8F0 / #9A9AB0`; radios `card 14 / btn 10 / pill 20`; Inter;
  `<html class="dark">`).
- `AppShell` + `BottomTabs` (5: Inicio · Materias · Recordat. · Convenios · Perfil).
- Onboarding: `/login`, `/registro`, `/onboarding/carrera`.
- Primitivos base (Tier 0): `Button`, `Field`, `TextInput`, `Select`, `NumberInput`,
  `Switch`, `Chip`, `Card`, `Modal`, `Tabs`, `IconButton`.
- `features/catalogo/`: `getCarreras()`, `useCarreras()`.

> Si algo de esto falta o está a medias, se completa antes de arrancar las tareas de abajo.

---

## 🧩 Módulos compartidos — un dueño, los demás importan

Nadie duplica ni pisa archivos: cada módulo tiene **un dueño** que lo escribe completo; el
resto lo importa. Si necesitás algo que "le toca" a otro módulo, se lo pedís al dueño.

| Módulo | Dueño | Lo consumen también |
|--------|-------|---------------------|
| `components/FormModal` + `EntityForm` | **Int. 1** | 2, 3, 4 |
| `components/` kit UX (`ListState`, `Paginador`, `EmptyState`, `ErrorState`, `Skeleton`, `ConfirmDialog`, `Toaster`/`useToast`, `useApiForm`) | **Int. 1** | 2, 3, 4 |
| `features/catalogo/` — `getMateriasDeCarrera(id)` (además de `getCarreras`, ya hecho) | **Int. 2** amplía | Int. 2 |
| `features/materias/` — `service.ts`/`hooks.ts` (mis materias, promedio, cursada CRUD) + `MateriaCard`, `ByteWidget`, `PromedioCard`, `estadoLabel`, `materiaUsuarioSpec` | **Int. 2** | Int. 3 (`materiaUsuarioSpec`) |
| `features/materia-detalle/` — `getMateria`, `getCorrelativas` + `CorrelativaItem` | **Int. 3** | — |
| `features/recursos/` — `service.ts`/`hooks.ts` + `RecursoCard` + `recursoSpec` | **Int. 3** | — |
| `features/recordatorios/` — `service.ts`/`hooks.ts` (`getRecordatorios(filtros)`, crear, borrar) + `RecordatorioCard` + `recordatorioSpec` | **Int. 4** | Int. 3 (sección por materia), Int. 2 (próximos en Inicio) |
| `features/convenios/` — `getConvenios`, `getTalentoTech` + hooks | **Int. 1** | — |
| `features/perfil/` — `getAuthMe`, `updateAuthMe` + hooks + `PerfilHeader` | **Int. 4** | — |

`GET /recordatorios/` es el único endpoint que usan dos pantallas (agenda de Int. 4 y
sección por materia de Int. 3): **una sola** `features/recordatorios/`, dueño Int. 4, con
`getRecordatorios(filtros)` que cubre los dos casos.

---

## 📊 Tareas por integrante

### 🧱 Integrante 1 — INFRA COMPARTIDA + CONVENIOS
**Prioridad:** ALTA · **Días:** 3 · **Lo del día 1–2 desbloquea a los otros 3.**

1. **`<FormModal>` + `<EntityForm>` genéricos** (`src/components/`)
   - `<FormModal spec={fieldSpec} initial={item?} onClose>`: modal sobre overlay oscuro,
     título del `spec`, campos armados desde `spec.fields`, botones Cancelar / Guardar.
   - `<EntityForm>`: recorre `spec.fields` y arma un `<Field>` por cada uno
     (`text` / `number` / `select` / `switch` / `datetime` / `url`), con `lockOnEdit`.
   - Al guardar: `spec.submit.create(v)` o `.update(id, v)`. Éxito → cierra, toast,
     invalida `spec.invalidates`. `422` → `errors[]` a los campos (`onError: 'fields'`);
     `409` / `403` → toast.
   - Forma del `fieldSpec` y los 3 ejemplos: `docs/INTEGRACION_FRONT.md` §2.9.

2. **Kit de UX transversal** (`src/components/`)
   - `<Toaster>` + `useToast()` (muestra `ApiError.detail`).
   - `useApiForm()` (de `ApiError.errors[]` → `fieldErrors`).
   - `<ListState>` (loading→`<Skeleton>` · error→`<ErrorState onRetry>` · vacío→`<EmptyState>` · ok→children).
   - `<Skeleton>`, `<EmptyState>`, `<ErrorState>`, `<ConfirmDialog>`,
     `<Paginador>` (`Paginated<T>` + `onPageChange`).

3. **`features/convenios/` + pantalla `/convenios`** (arquetipo Lista con Tabs)
   - `service.ts`: `getConvenios(params)`, `getTalentoTech(params)` + `hooks.ts`.
   - Tab Universidades (`GET /convenios/`, `/convenios/carrera/{id}`) y Tab TalentoTech
     (`GET /talentotech/`, `/talentotech/carrera/{id}`, `/talentotech/categoria/{cat}`).
   - Solo lectura, link externo (`link_info` / `link_inscripcion`), con `<Paginador>`.

4. **Buffer:** README del front (correr, `.env`, `npm run gen:api`), tests de un form con `errors[]`.

**🚫 NO crees:** ningún `service.ts` de materias, detalle de materia, recursos,
recordatorios ni perfil — cada uno tiene dueño (Int. 2 / 3 / 4). Vos solo hacés
`components/*` compartido y `features/convenios/`.

**Entregables:**
- [ ] `<FormModal>` + `<EntityForm>` publicados **día 1**
- [ ] Kit de UX publicado **día 1**
- [ ] `/convenios` (2 tabs, solo lectura) con estados de carga/vacío/error

---

### 📚 Integrante 2 — MATERIAS + INICIO
**Prioridad:** ALTA · **Días:** 4 · Depende del `<FormModal>` de Int. 1.

1. **`features/catalogo/` — ampliación**
   - Agregar `getMateriasDeCarrera(carreraId)` (`GET /materias/carrera/{id}`) +
     `useMateriasDeCarrera(id)`. (`getCarreras`/`useCarreras` ya existen.)

2. **`features/materias/` — `service.ts` + `hooks.ts`**
   - `service.ts`: `getMisMaterias(page?)`, `getPromedio()`, `createCursada(body)`,
     `updateCursada(id, body)`, `deleteCursada(id)` — tipadas con
     `Cursada` / `CursadaCreate` / `CursadaUpdate` / `Promedio`.
   - `hooks.ts`: `useMisMaterias`, `usePromedio`, `useCrearCursada`, `useEditarCursada`,
     `useBorrarCursada` (invalidan `['mis-materias']` + `['promedio']`).

3. **Componentes de materia + `materiaUsuarioSpec`**
   - `<MateriaCard>` (nombre + `<Chip>` de estado + nota), `<ByteWidget>` (`{ aprobadas, total }`),
     `<PromedioCard>` (`promedio | null`), `estadoLabel(cursada)` (§2.13 del doc).
   - `materiaUsuarioSpec`: select `useMateriasDeCarrera(usuario.carrera_id)`, toggle `cursando`,
     notas 1–10. `submit.create` → `createCursada` · `submit.update` → `updateCursada`.

4. **Pantalla `/materias`** (arquetipo Lista)
   - `useMisMaterias` + `usePromedio`. `<ByteWidget>` / `<PromedioCard>` arriba,
     `<MateriaCard>` en lista. Chips de filtro por estado (filtran en cliente).
   - FAB `+` → `<FormModal spec={materiaUsuarioSpec}>`. Maneja `409` (ya cargada / otra
     carrera) y `422` (nota 1–10).

5. **Pantalla `/` Inicio** (arquetipo Panel)
   - Reusa tus `<ByteWidget>` / `<PromedioCard>` + `useMisMaterias` + `usePromedio`.
   - Próximos recordatorios: **importa** `useRecordatorios({ desde: hoy })` de
     `features/recordatorios/` (Int. 4). Solo lectura; tap → su materia.
   - Accesos rápidos a las materias.

6. **(Si sobra) ABM de catálogo admin** — `/admin/catalogo`, solo `usuario.rol === 'admin'`.

**🚫 NO crees:** `<FormModal>` / `<EntityForm>` ni el kit de UX (Int. 1).
`getMateria` / `getCorrelativas` / nada de recursos (Int. 3).
`features/recordatorios/`, `<RecordatorioCard>`, `recordatorioSpec` (Int. 4) — para los
"próximos" del Inicio importás `useRecordatorios` de Int. 4.

**Entregables:**
- [ ] `features/materias/` (`service.ts` + `hooks.ts`) + `getMateriasDeCarrera`
- [ ] `<MateriaCard>` / `<ByteWidget>` / `<PromedioCard>` / `materiaUsuarioSpec` publicados
- [ ] `/materias` con lista, filtro por estado, promedio/Byte y alta/edición vía modal
- [ ] `/` Inicio funcionando

---

### 🎓 Integrante 3 — DETALLE DE MATERIA + RECURSOS
**Prioridad:** ALTA · **Días:** 4 · Depende del `<FormModal>` de Int. 1 y de
`features/recordatorios/` de Int. 4.

1. **`features/materia-detalle/` — `service.ts` + `hooks.ts`**
   - `getMateria(id)`, `getCorrelativas(id)` + `useMateria(id)`, `useCorrelativas(id)`.
   - `<CorrelativaItem>` (usa `requiere` embebido, sin llamada extra).

2. **`features/recursos/` — `service.ts` + `hooks.ts` + componentes**
   - `getRecursosDeMateria(materiaId)`, `createRecurso(body)`, `updateRecurso(id, body)`,
     `deleteRecurso(id)` + hooks (invalidan `['recursos-materia', id]`).
   - `<RecursoCard>` (ícono por tipo + título + link externo; **Editar** y **borrar** solo
     si `recurso.usuario_id === usuario.id`, manejar `403` igual).
   - `recursoSpec(materiaId)`: `titulo` (1–150), `url` (http/https), `descripcion`, `tipo`.
     `submit` → `createRecurso` / `updateRecurso` (**sin** `usuario_id`).

3. **Pantalla `/materias/:id`** (arquetipo Detalle)
   - `useMateria(id)` + `useCorrelativas(id)` + `useRecursosDeMateria(id)` +
     `useRecordatorios({ materia_id: id })` *(hook de Int. 4)*.
   - Meta: badge de estado (`estadoLabel`, de Int. 2) + notas + botón **"Editar notas"**
     → `<FormModal spec={materiaUsuarioSpec}>` *(spec de Int. 2)* con `initial` = la cursada.
   - `<Section>` Correlativas → `<CorrelativaItem>`.
   - `<Section>` Recursos → `<RecursoCard>` + botón **"Agregar recurso"** (`<FormModal spec={recursoSpec(id)}>`).
   - `<Section>` Recordatorios → `<RecordatorioCard>` *(de Int. 4)* con **Editar** y **borrar**;
     botón **"Agregar recordatorio"** → `<FormModal spec={recordatorioSpec(id)}>` *(de Int. 4)*.

**🚫 NO crees:** `materiaUsuarioSpec`, `useMisMaterias`, `usePromedio`, `estadoLabel`,
`<ByteWidget>` (Int. 2) — los **importás**. `features/recordatorios/`, `<RecordatorioCard>`,
`recordatorioSpec`, `useRecordatorios` (Int. 4) — los **importás**. `<FormModal>` / kit UX (Int. 1).

**Entregables:**
- [ ] `features/materia-detalle/` + `features/recursos/` (`service.ts` + `hooks.ts`)
- [ ] `<RecursoCard>` + `recursoSpec` + `<CorrelativaItem>` publicados
- [ ] `/materias/:id` con correlativas + recursos (ownership) + recordatorios de la materia
- [ ] Alta/edición de recurso y de recordatorio vía el **mismo** `<FormModal>`

---

### 🔔 Integrante 4 — RECORDATORIOS + AGENDA + PERFIL
**Prioridad:** ALTA · **Días:** 4 · **`features/recordatorios/` es compartido → publicarlo día 1–2.**

1. **`features/recordatorios/` — módulo completo** (lo consumen Int. 3 y el Inicio de Int. 2)
   - `service.ts`: `getRecordatorios(filtros)` (un solo fetch a `GET /recordatorios/`, los
     `filtros` — `tipo`, `desde`, `hasta`, `materia_id`, `page` — cubren agenda global *y*
     sección por materia), `createRecordatorio(body)`, `deleteRecordatorio(id)`.
   - `hooks.ts`: `useRecordatorios(filtros)`, `useCrearRecordatorio`, `useBorrarRecordatorio`
     (invalidan `['recordatorios']`).
   - `<RecordatorioCard>` (dot por tipo + título + fecha; props para modo "con acciones"
     [Editar/borrar] o "solo lectura" [Inicio]).
   - `recordatorioSpec(materiaId?)`: `titulo`, `fecha` (**futura**, `422` al campo), `tipo`
     (`parcial`/`tp`/`final`/`otro`). `submit.create` → `createRecordatorio`.
     **Editar:** no hay `PATCH` todavía → `DELETE` + `POST` (ver *Dependencias del backend*).

2. **Pantalla `/recordatorios` — Agenda global** (arquetipo Lista)
   - `useRecordatorios({ tipo, desde, hasta, materia_id })` (orden fecha desc), agrupada por
     semana en cliente. Dot por tipo. Swipe / `<ConfirmDialog>` para borrar.
   - FAB `+` → `<FormModal spec={recordatorioSpec()}>` (sin materia fija; select de materia
     opcional acá).

3. **`features/perfil/` + pantalla `/perfil`** (arquetipo Panel)
   - `service.ts`: `getAuthMe()`, `updateAuthMe(body)` + `useAuthMe`, `useEditarPerfil`.
   - `<PerfilHeader>` (avatar + nombre + email + carrera).
   - Editar **nombre** + **carrera** (select `useCarreras`) → `updateAuthMe` (`PATCH /auth/me`,
     ver *Dependencias del backend*; mientras tanto solo visual).
   - Botón **"Cerrar sesión"** → `logout()` → `/login`.

**🚫 NO crees:** `useMisMaterias`, `usePromedio`, `<ByteWidget>`, `<PromedioCard>` (Int. 2).
`getMateria` / `getCorrelativas` / recursos (Int. 3). `<FormModal>` / kit UX (Int. 1).
Para el select de carrera del perfil usás `useCarreras` (ya existe).

**Entregables:**
- [ ] `features/recordatorios/` completo publicado **día 1–2** (lo usan Int. 2 e Int. 3)
- [ ] `/recordatorios` agenda global con filtros + alta con fecha futura
- [ ] `features/perfil/` + `/perfil` con `getAuthMe`, editar y cerrar sesión

---

## 🔌 Dependencias del backend (pedir a Sprint 2)

| Falta | Para | Workaround mientras tanto |
|-------|------|---------------------------|
| `PATCH /recordatorios/{id}` + schema `RecordatorioUpdate` | Botón "editar" de recordatorio (Int. 4 / Int. 3) | `DELETE` + `POST` (cambia el `id`) |
| `PATCH /auth/me` con `{ nombre?, carrera_id? }` | Editar perfil (Int. 4) | Campos solo visuales |

---

## 📅 Cronograma (3–4 días)

### Día 1
- **Int. 1:** `<FormModal>` + `<EntityForm>` + kit de UX. *(desbloquea a todos)*
- **Int. 4:** `features/recordatorios/` (`service.ts`/`hooks.ts` + `<RecordatorioCard>` + `recordatorioSpec`). *(desbloquea a Int. 2 e Int. 3)*
- **Int. 2:** `features/catalogo/` (ampliación) + `features/materias/` (`service.ts`/`hooks.ts`).
- **Int. 3:** `features/materia-detalle/` + `features/recursos/` (`service.ts`/`hooks.ts`); maqueta de `/materias/:id` con mock.

### Día 2
- **Int. 1:** `features/convenios/` + `/convenios`.
- **Int. 2:** `<MateriaCard>`/`<ByteWidget>`/`<PromedioCard>` + `materiaUsuarioSpec` + `/materias`.
- **Int. 3:** `<RecursoCard>` + `recursoSpec` + `/materias/:id` real (secciones Correlativas y Recursos).
- **Int. 4:** `/recordatorios` agenda global.

### Día 3
- **Int. 2:** `/` Inicio (importa `useRecordatorios` de Int. 4).
- **Int. 3:** sección Recordatorios en `/materias/:id` (importa de Int. 4).
- **Int. 4:** `features/perfil/` + `/perfil`.
- **Int. 1:** README del front + tests + buffer.

### Día 4
- Todos: prueba de punta a punta contra el backend local (`python seed.py`), pulido, PRs.

---

## ✅ Criterios de aceptación

1. **Auth y shell** (ya): login / registro / elegí carrera / logout; `<RutaProtegida>`;
   `401` desloguea; 5 tabs; tokens de Tailwind del design system.
2. **Materias:** ver / crear / editar / borrar materias con notas vía `<FormModal>`;
   badge de estado derivado; promedio y Byte reaccionan.
3. **Detalle de materia:** correlativas + recursos (con ownership) + recordatorios de la
   materia, con alta/edición por el **mismo** `<FormModal>`.
4. **Agenda / convenios / perfil:** agenda global con filtros; convenios solo lectura;
   perfil con `getAuthMe` y "cerrar sesión".
5. **Contrato:** toda lista `{items,total,…}` + `<Paginador>`; `detail` → toast;
   `errors[]` → campos; nunca `usuario_id` en las URLs.
6. **Capas:** cada feature tiene `service.ts` + `hooks.ts`; los componentes usan hooks,
   nadie llama a `apiClient` directo.
7. **Sin duplicados:** cada módulo compartido tiene un solo dueño (ver tabla). Nadie
   reescribe un `service.ts` de otro feature.
8. **Un solo pop-up:** todos los formularios son `<FormModal>` + `fieldSpec`.
9. **Proceso:** cada feature en `feature/<nombre>`, PR con ≥ 1 review.

---

## 🚀 Bonus (si sobra tiempo)

1. **Optimistic updates** en materias y recordatorios.
2. **Tests** con Vitest + Testing Library: flujo de auth y un form con `errors[]`.
3. **Deploy del front** (Vercel / Netlify / Pages) apuntando al backend desplegado.
4. **Aviso de expiración** del token ~1 min antes de las 24 h.
5. **PWA**: manifest + service worker (cache de TanStack Query para offline).

---

## 📞 Coordinación

### Daily (10 min)
¿Qué hice ayer? ¿Qué haré hoy? ¿Blockers?

### Dependencias críticas
- **Int. 1** entrega `<FormModal>` + `<EntityForm>` + kit de UX **día 1** (los usan 2, 3, 4).
- **Int. 4** entrega `features/recordatorios/` completo **día 1–2** (lo usan Int. 3 y el Inicio de Int. 2).
- **Int. 2** entrega `materiaUsuarioSpec` + `<ByteWidget>`/`<PromedioCard>` **día 2** (los usa Int. 3 y su propio Inicio).

### Git Flow (repo del front)
```bash
git checkout main && git pull
git checkout -b feature/tu-nombre-tarea
git commit -m "feat: descripción clara"
git push -u origin feature/tu-nombre-tarea
# PR → main, review de ≥1 compañero
```
