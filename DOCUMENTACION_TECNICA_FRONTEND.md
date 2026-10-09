# Documentación Técnica - miIFTS Frontend

## Resumen del Proyecto
Aplicación web académica para estudiantes del IFTS. SPA React 19 + TypeScript + Vite + Tailwind CSS v4 + PWA. Consume API REST FastAPI (`VITE_API_URL=http://localhost:8000`).

---

## Stack Tecnológico
| Capa | Tecnología | Versión |
|------|------------|---------|
| Runtime | React | 19.2.8 |
| Lenguaje | TypeScript | 6.0.2 |
| Build | Vite | 8.2 |
| Estilos | Tailwind CSS | 4.3.3 (@tailwindcss/vite) |
| HTTP | Fetch nativo + wrapper `apiClient` | - |
| Autenticación | JWT HS256 24h (localStorage + memoria) | - |
| PWA | vite-plugin-pwa | 1.3 (autoUpdate) |
| Testing | Vitest + RTL + MSW | 5.0.2 (diferido) |
| Lint/Format | ESLint 10.8 / oxfmt | - |

---

## Arquitectura General
```
src/
├── api/                    # Cliente HTTP + tipos generados
│   ├── client.ts           # apiClient único (baseURL, Auth header, parser ApiError, 401→logout)
│   ├── schema.d.ts         # Tipos generados desde openapi.json (npx openapi-typescript)
│   └── types.ts            # Tipos hand-written + alias de schema.d.ts
├── auth/                   # Autenticación y sesión
│   ├── AuthContext.tsx     # Fuente única de verdad (token, usuario, timers expiración, login/registro/logout)
│   ├── api.ts              # Endpoints auth (login, registro, me, forgot/reset password, change-password)
│   └── storage.ts          # Helpers localStorage (token, usuario, expiración)
├── components/             # UI reutilizable
│   ├── ListState.tsx       # Loading / Error / Empty + retry
│   ├── Paginador.tsx       # Paginación genérica Paginated<T>
│   ├── FormModal.tsx       # Modal de formularios (create/edit)
│   ├── ConfirmDialog.tsx   # Confirmación borrado
│   ├── Modal.tsx           # Modal base
│   ├── Toaster.tsx         # Toast notifications
│   └── ...
├── features/               # Funcionalidades por dominio
│   ├── auth/               # Guards (RutaProtegida, RutaAdmin) + hooks login
│   ├── catalogo/           # Carreras + Materias (lectura pública)
│   ├── catalogo-admin/     # ABM Carreras + Materias + Correlativas (admin)
│   ├── convenios/          # Convenios + TalentoTech (lectura estudiante)
│   ├── convenios-admin/    # CRUD Convenios (admin)
│   ├── materias/           # Mis cursadas, promedio, Inicio, detalle
│   ├── materia-detalle/    # Detalle materia + correlativas + recursos + recordatorios
│   ├── perfil/             # Perfil editable + cambio password + accesibilidad
│   ├── recordatorios/      # Agenda global + push notifications
│   └── admin/              # Shell Admin (tabs Catálogo / Convenios)
├── hooks/                  # Hooks transversales
│   ├── useApiForm.ts       # Formularios con mapeo 422→fieldErrors
│   ├── useAsyncQuery.ts    # Fetch simple con loading/error/data/refetch
│   ├── useToast.ts         # Notificaciones toast
│   └── usePush.ts          # Push notifications (Service Worker + VAPID)
├── lib/                    # Utilidades
│   ├── apiClient.ts        # (alias a api/client.ts)
│   ├── preferencias.ts     # Tema/accesibilidad (CSS vars)
│   └── push.ts             # Lógica push nativa
└── App.tsx                 # Router en memoria (switch screen) + Shell responsive
```

---

## Funcionalidades Mapeadas

### 1. Autenticación (Auth)
**Pantallas**: Login, Registro (2 pasos: datos + carrera), Olvidé contraseña, Reset password
**Endpoints**: `POST /auth/login`, `POST /auth/registro`, `GET /auth/me`, `POST /auth/forgot-password`, `POST /auth/reset-password`
**Flujo**: Registro → Login automático → Guarda `access_token` + `usuario` en localStorage/memoria → Interceptor 401 limpia sesión y redirige a login
**Tecnologías**: `AuthContext` (React Context), `apiClient` (fetch + interceptors), JWT 24h sin refresh, validación cliente password (≥8, letra+número)

### 2. Catálogo Público (Estudiante)
**Pantallas**: Lista carreras, Detalle carrera, Lista materias por carrera, Buscar materias, Detalle materia + correlativas
**Endpoints**: `GET /materias/carreras`, `GET /materias/carreras/{id}`, `GET /materias/carrera/{carrera_id}`, `GET /materias/buscar`, `GET /materias/{id}`, `GET /materias/correlativas/{id}`
**Features**: Paginación `Paginated<T>`, filtros (año, cuatrimestre), correlativas con `requiere`
**Tecnologías**: `features/catalogo/service.ts` + `hooks.ts`, `useAsyncQuery`, `ListState` + `Paginador`

### 3. Mis Cursadas + Promedio (Estudiante)
**Pantallas**: Inicio (dashboard), Mis Materias (lista + filtros), Detalle materia
**Endpoints**: `GET /materias/usuario/{id}`, `GET /materias/promedio/{id}`, `POST /materias/usuario`, `PATCH/DELETE /materias/cursada/{id}`
**Reglas**: Sin `usuario_id` en body (sale del token), notas 1-10, estado derivado (cursando → aprobada con nota_final → pendiente), 409 duplicado/carrera distinta
**Componentes**: `MateriaCard`, `ByteWidget` (progreso visual), `PromedioCard`, `CursadaFormModal`, chips filtro cliente
**Tecnologías**: `features/materias/hooks.ts` (`useMisMaterias`, `usePromedio`, `useBorrarCursada`), `estado.ts` (label/badge), `FormModal` + `materiaUsuarioSpec`

### 4. Recursos (Estudiante - dueño)
**Pantallas**: Lista con filtros (materia, tipo, fechas), Detalle, Crear/Editar/Borrar propios
**Endpoints**: `GET /recursos/`, `GET /recursos/materia/{id}`, `GET /recursos/usuario/{id}`, `POST/PUT/DELETE /recursos/{id}`
**Validaciones**: `titulo` 1-150, `url` HttpUrl, `tipo` pdf|video|link, ownership 403 si ajeno
**Tecnologías**: `features/recursos/service.ts` + `hooks.ts`, `EntityForm` + `recursoSpec`

### 5. Convenios + TalentoTech (Lectura pública)
**Pantallas**: Tabs "Universidades" / "Talento Tech", cards con logo + requisitos + botón "Más info" (abre link externo)
**Endpoints**: `GET /convenios/`, `GET /convenios/carrera/{id}`, `GET /talentotech/`, `GET /talentotech/categoria/{cat}`
**Tecnologías**: `features/convenios/service.ts` + `hooks.ts`, `ListState` + `Paginador`, mapeo a `ConvenioItem` (forma UI)

### 6. Recordatorios + Push Notifications (Estudiante)
**Pantallas**: Agenda global (agrupada "Esta semana" / "Más adelante"), FAB crear, editar/borrar cards
**Endpoints**: `GET /recordatorios/`, `POST /recordatorios/`, `DELETE /recordatorios/{id}`
**Push**: Service Worker (`public/sw.js`), VAPID, suscripción navegador, badge en nav "Recordat."
**Tecnologías**: `features/recordatorios/hooks.ts` (`useRecordatorios`, `useBorrarRecordatorio`), `usePush.ts` (SW + VAPID), `RecordatorioCard`, `FormModal` + `recordatorioSpec`

### 7. Perfil de Usuario (Estudiante + Admin)
**Pantallas**: Perfil (datos + progreso carrera + accesibilidad + logout), Modal "Cambiar contraseña"
**Endpoints**: `GET /auth/me`, `PATCH /auth/me` (solo `nombre`/`apellido`), `PATCH /auth/password` (cambio password logueado)
**Reglas**: Email y carrera **readOnly** (backend ignora email, carrera bloqueado por negocio), validación 422→fields, 409 email duplicado→toast, sync automático `AuthContext.usuario` + localStorage sin reload
**Accesibilidad**: Panel con selector de tema (claro/oscuro/sistema), tamaño fuente, alto contraste
**Tecnologías**: `features/perfil/hooks.ts` (`useAuthMe`), `useApiForm`, `CambiarPasswordModal`, `AccesibilidadPanel` (CSS vars en `index.css`)

### 8. Panel Admin (Solo rol=admin)
**Pantallas**: Shell con tabs "Catálogo" / "Convenios"
- **Catálogo**: ABM Carreras + Materias (existente S4-10) + Correlativas (nuevo: 2 selects materia/requiere, excluye propia, 409 ciclo/duplicado)
- **Convenios**: CRUD completo sobre forma cruda backend (`institucion`, `carrera_destino`, `descripcion`, `link_info` URL validada cliente, `carrera_id` select)
**Acceso**: Nav item "Admin" reemplaza nav estudiante (solo ve Admin + Perfil), login/rehidratación aterriza directo en panel
**Tecnologías**: `features/catalogo-admin/`, `features/convenios-admin/`, `features/admin/AdminScreen.tsx`, tipos generados `openapi-typescript` (`CarreraCreate/Update`, `MateriaCreate/Update`, `CorrelativaCreate`, `ConvenioCreate`)

---

## Patrones Transversales

| Patrón | Implementación |
|--------|----------------|
| **Wrapper HTTP único** | `apiClient` en `api/client.ts`: baseURL, Bearer token, parser `ApiError {detail, errors[]}`, 401→`unauthorizedHandler` (logout), no parse 204 |
| **Autenticación** | `AuthContext` fuente única; rehidratación `GET /auth/me` en mount; timers expiración (warn 60s + logout auto) |
| **Paginación** | `Paginated<T> = {items,total,page,per_page,total_pages}`; `Paginador` reutilizable; `per_page` default 20, clamp 1-100 |
| **Formularios** | `FormModal` + `EntityForm` + `*Spec.ts` (fieldSpec: select, switch, number, url, password); `useApiForm` mapea 422 `errors[]` → `fieldErrors` por campo |
| **Estados UI** | `ListState` (loading/error/empty + retry), `Skeleton` loading, `ErrorState` con retry, `EmptyState` con acción |
| **Navegación** | `App.tsx` usa `switch(screen)` en memoria (no React Router); `SidebarNav` (md+) + `BottomNav` (mobile); `showNav` oculta en pantallas públicas |
| **Temas/Accesibilidad** | CSS variables en `index.css` (`--c-bg`, `--c-card`, `--c-primary`, etc.); `preferencias.ts` persiste en localStorage + aplica al `<html>` |
| **Tipado** | `openapi-typescript` genera `schema.d.ts` desde `openapi.json`; `api/types.ts` alias + hand-written; `npm run gen:api` |

---

## Decisiones Arquitectónicas Clave (ver `docs/context/decisions.md`)

- **D004**: Wrapper único `apiClient` (no fetch suelto)
- **D005**: JWT 24h en localStorage + memoria, sin refresh
- **D008**: Paginación genérica `Paginated<T>`
- **D014**: Reset password sin router: lee `token` de `window.location.search` en `App()` mount
- **D015**: `suppressUnauthorizedRedirect` en `apiClient` para `PATCH /auth/password` (401 = "password actual no coincide", no logout)
- **D016**: `PATCH /auth/me` solo `nombre`/`apellido` (backend ignora email, carrera bloqueado)
- **D017**: Cambio password logueado via `PATCH /auth/password` (no `/auth/change-password` que nunca existió)
- **D019**: Admin nav **reemplaza** al de estudiante (no se suma); aterriza directo en panel
- **D020**: `convenios-admin` feature nueva, no reusa `convenios` (lectura)

---

## Variables de Entorno
```env
VITE_API_URL=http://localhost:8000    # Base URL API (sin trailing slash)
# VITE_DEMO_MODE=false                # Deshabilitado en prod (sin mocks)
```

---

## Scripts Principales
```bash
npm run dev        # Vite dev server (HMR)
npm run build      # Build producción (dist/)
npm run preview    # Preview build
npm run format     # oxfmt
npm run test       # Vitest (watch)
npm run test:run   # Vitest (CI)
npm run gen:api    # Genera tipos desde openapi.json (backend debe estar corriendo)
```

---

## Criterios de Aceptación Globales
- [ ] Auth flujo completo + 401 interceptor + carrera select en registro
- [ ] 5+ pantallas navegables con guards y paginación reutilizable
- [ ] Ownership y 403/404/409/422 manejados (toast + field errors)
- [ ] Wrapper único + fecha futura 422 + DELETE 204 sin parse
- [ ] Olvidé contraseña: link en Login → email → éxito siempre; reset con token query param; 400 token inválido vuelve a "olvidé"
- [ ] Perfil editable: `PATCH /auth/me` nombre/apellido persiste + sync sin reload; email/carrera readOnly; cambio password modal `PATCH /auth/password` (401 no desloguea)
- [ ] Admin: nav rol-gated, tabs Catálogo/Convenios, correlativas + CRUD convenios validados
- [ ] Responsive: shell fluido `max-w-lg sm:max-w-2xl lg:max-w-5xl`, grids adaptables, sin `430px` fijo
- [ ] `npm run build && npm run lint` verdes