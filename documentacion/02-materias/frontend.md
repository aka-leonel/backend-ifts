# Materias - Frontend

## Features

| Feature | Carpeta | Pantallas |
|---------|---------|-----------|
| Catálogo Público | `features/catalogo/` | Carreras, Detalle carrera, Materias por carrera, Buscar, Detalle materia + correlativas |
| Mis Cursadas | `features/materias/` | Dashboard (Inicio), Mis Materias (lista + filtros), Detalle materia |
| Admin Catálogo | `features/catalogo-admin/` | ABM Carreras, ABM Materias, Correlativas (2 selects + validación ciclos) |

## Catálogo Público (`features/catalogo/`)

- **Servicio:** `catalogoService` → `GET /carreras`, `/carrera/{id}/materias`, `/buscar`, `/{id}`, `/correlativas/{id}`
- **Hooks:** `useCarreras`, `useMateriasByCarrera`, `useBuscarMaterias`, `useMateria`, `useCorrelativas` (todos `useAsyncQuery`)
- **Componentes:** `CarreraCard`, `MateriaCard`, `CorrelativaList`, `BuscadorMaterias` (debounce 300ms)
- **Pantallas:** `CarrerasScreen` (grid + paginador), `CarreraDetalleScreen` (tabs Materias/Info), `MateriaDetalleScreen` (info + correlativas + botón "Agregar a mis cursadas"), `BuscarMateriasScreen`

## Mis Cursadas (`features/materias/`)

- **Estado derivado (`estado.ts`):** Mapea `estado` string → `{label, color, icon}` (cursando=azul, promocionada=verde, aprobada=emerald, desaprobada=rojo, pendiente=gris)
- **ByteWidget:** SVG circular compartido (MateriaCard, PromedioCard, Detalle)
  - cursando: arco según notas cargadas
  - promocionada/aprobada: 100% verde
  - desaprobada: 100% rojo
  - pendiente: 0% gris
- **Hooks:** `useMisMaterias`, `usePromedio`, `useAgregarCursada`, `useActualizarCursada`, `useBorrarCursada`
- **Spec (`materiaUsuarioSpec`):** select materias no cursadas de su carrera, switch cursando, number 1-10 step 0.25 (parcial1, parcial2, examen_final)
- **Pantallas:**
  - `InicioScreen`: `PromedioCard` + `ProgresoCarrera` + próximos recordatorios
  - `MisMateriasScreen`: chips filtro (Todas/Cursando/Promocionadas/Aprobadas/Desaprobadas/Pendientes) + `MateriaCard` + FAB crear
  - `MateriaDetalleScreen`: info + correlativas + `CursadaFormModal` (editar notas) + borrar

## Admin (`features/catalogo-admin/`)

- **Tabs:** Carreras / Materias / Correlativas
- **Carreras/Materias:** CRUD estándar con `FormModal` + specs
- **Correlativas Admin:** `CorrelativasAdminScreen`
  - Lista existentes (con `requiere` embebido)
  - FAB → `FormModal` + `correlativaAdminSpec`
  - **2 Selects** con misma lista materias: `materia_id` / `requiere_id`
  - Validación cliente: `requiere_id !== materia_id`
  - Backend valida ciclos reales (DFS) → 409 toast

## Componentes Compartidos

| Componente | Uso |
|------------|-----|
| `ListState` | Loading/Error/Empty + retry en todas las listas |
| `Paginador` | Paginación genérica |
| `FormModal` + `EntityForm` | Create/Edit (cursadas, carreras, materias, correlativas) |
| `ByteWidget` | Progreso visual circular |
| `MateriaCard` | Catálogo + Mis Cursadas |
| `PromedioCard` | Dashboard + header Mis Materias |
| `ConfirmDialog` | Delete confirmations |
| `Toaster` | Feedback éxito/error |