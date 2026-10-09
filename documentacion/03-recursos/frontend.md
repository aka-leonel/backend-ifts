# Recursos - Frontend

## Pantallas

| Pantalla | Ruta | Descripción |
|----------|------|-------------|
| Lista Recursos | `/recursos` | Grid con filtros (materia, tipo, fechas), paginación, FAB crear |
| Detalle Recurso | `/recursos/:id` | Vista completa + botones editar/borrar (solo dueño) |
| Crear/Editar | Modal `FormModal` | `EntityForm` con `recursoSpec` |

## Servicio (`features/recursos/service.ts`)

```typescript
recursosService.getAll(params, filters?)     // GET /recursos/ con query params
recursosService.getById(id)                   // GET /recursos/{id}
recursosService.getByUsuario(usuarioId, params)
recursosService.getByMateria(materiaId, params)
recursosService.create(data)                  // POST /recursos/
recursosService.update(id, data)              // PUT /recursos/{id}
recursosService.delete(id)                    // DELETE /recursos/{id}
```

## Hooks (`hooks.ts`)

- `useRecursos(params, filters)` → `useAsyncQuery`
- `useRecursosByUsuario(usuarioId, params)`
- `useRecurso(id)`
- `useCrearRecurso()` / `useActualizarRecurso(id)` / `useBorrarRecurso()` → `useApiForm`

## Spec (`recursoSpec.ts`)

```typescript
recursoSpec = [
  { name: "materia_id", label: "Materia", type: "select", required: true, options: [] }, // materias carrera usuario
  { name: "titulo", label: "Título", type: "text", required: true, maxLength: 150 },
  { name: "url", label: "URL", type: "url", required: true },
  { name: "descripcion", label: "Descripción", type: "textarea", required: true, rows: 4 },
  { name: "tipo", label: "Tipo", type: "select", required: false,
    options: [{value:"pdf",label:"PDF"}, {value:"video",label:"Video"}, {value:"link",label:"Enlace"}, {value:"documento",label:"Documento"}, {value:"otro",label:"Otro"}] }
]
```

## Pantalla Lista (`RecursosScreen.tsx`)

- **Toolbar filtros:** Select Materia, Select Tipo, DateRangePicker (desde/hasta), Botón Limpiar
- **Lista:** `ListState` + `RecursoCard` grid + `Paginador`
- **FAB:** Abre `FormModal` create
- **EmptyState:** "No hay recursos" + botón "Crear recurso"

## Card (`RecursoCard.tsx`)

- `TipoBadge` chip colorido (pdf=rojo, video=azul, link=verde, documento=naranja, otro=gris)
- Título, descripción (line-clamp-2), `MateriaChip`, `TimeAgo`
- Acciones: link "Abrir →" (target=_blank), botones editar/borrar **solo si dueño** (`recurso.usuario_id === currentUser.id`)

## Detalle (`RecursoDetalleScreen`)

- Info completa, tipo badge grande, link abrible, botones editar/borrar (solo dueño)

## Validaciones Cliente

| Campo | Regla |
|-------|-------|
| `materia_id` | Select obligatorio (opciones = materias carrera usuario) |
| `titulo` | Required, max 150 |
| `url` | Required, type="url" + pattern |
| `descripcion` | Required, textarea |
| `tipo` | Select opcional |

## Errores

| Backend | Frontend |
|---------|----------|
| 403 ownership | Toast error + botones editar/borrar ocultos |
| 404 | `ListState` error / toast |
| 422 url/titulo | `fieldErrors.url` / `fieldErrors.titulo` |
| 401 | `apiClient` → logout + redirect login |