# Convenios + TalentoTech - Frontend

## Features Separadas

| Feature | Carpeta | Descripción |
|---------|---------|-------------|
| Lectura Pública | `features/convenios/` | Tabs "Universidades" / "Talento Tech", cards con links externos |
| Admin CRUD | `features/convenios-admin/` | CRUD completo convenios |

---

## Lectura Pública (`features/convenios/`)

### Servicio (`service.ts`)

```typescript
conveniosService.getAll(params)                    // GET /convenios/
conveniosService.getByCarrera(carreraId, params)   // GET /convenios/carrera/{id}
conveniosService.getById(id)                       // GET /convenios/{id}

// TalentoTech
talentotechService.getAll(params)                  // GET /talentotech/
talentotechService.getByCarrera(carreraId, params) // GET /talentotech/carrera/{id}
talentotechService.getByCategoria(cat, params)     // GET /talentotech/categoria/{cat}
talentotechService.getById(id)                     // GET /talentotech/{id}
```

### Hooks → `useAsyncQuery` para cada método.

### Mapeo UI (`ConvenioItem` / `TalentoTechItem`)

```typescript
ConvenioItem: { id, institucion, carreraDestino, descripcion, linkInfo, carreraNombre, logoUrl? }
TalentoTechItem: { id, nombreCurso, categoria, descripcion, duracion, linkInscripcion, carreraNombre, badgeColor }
```

### Pantalla (`ConveniosScreen.tsx`)

- **Tabs:** "Universidades" / "Talento Tech"
- **ConveniosGrid:** `ConvenioCard` (logo + institucion + carreraDestino + descripción truncada + badge carrera + botón "Más info" → `window.open(linkInfo, "_blank")`)
- **TalentTechGrid:** `TalentTechCard` (badge categoría + nombreCurso + descripción + duracion + carreraNombre + botón "Inscribirme" → `window.open(linkInscripcion, "_blank")`)
- **ListState + Paginador** en cada tab

---

## Admin (`features/convenios-admin/`)

### Servicio (`service.ts`)

```typescript
adminConveniosService.getAll(params)
adminConveniosService.getById(id)
adminConveniosService.create(data)      // POST /convenios/
adminConveniosService.update(id, data)  // PUT /convenios/{id}
adminConveniosService.delete(id)        // DELETE /convenios/{id}
```

### Spec (`convenioAdminSpec.ts`)

```typescript
convenioAdminSpec = [
  { name: "carrera_id", label: "Carrera", type: "select", required: true, options: [] }, // dinámico
  { name: "institucion", label: "Institución", type: "text", required: true, maxLength: 150 },
  { name: "carrera_destino", label: "Carrera Destino", type: "text", required: true, maxLength: 150 },
  { name: "descripcion", label: "Descripción", type: "textarea", required: true, rows: 4 },
  { name: "link_info", label: "Link Información", type: "url", required: true }
]
```

### Pantalla (`ConveniosAdminScreen.tsx`)

- Lista paginada + `ListState` + `Paginador`
- FAB "Crear" → `FormModal` + `EntityForm` + `convenioAdminSpec`
- Acciones: Editar (PUT), Borrar (DELETE + `ConfirmDialog`)
- Validación: `link_info` tipo URL (type="url" + pattern)

## Validaciones Cliente (Admin)

| Campo | Regla |
|-------|-------|
| `institucion` | Required, max 150 |
| `carrera_destino` | Required, max 150 |
| `descripcion` | Required, textarea |
| `link_info` | Required, URL válida |
| `categoria` (TT) | Select sugerido (Programación, Data, UX, Diseño, Marketing, Otro) + custom |
| `duracion` (TT) | Required, max 50 (ej: "3 meses") |

## Categorías TalentoTech

- Backend: `String(20)` libre
- Frontend: Select con opciones conocidas + `allowCustom: true` en `EntityForm` para valor libre

## Errores

| Backend | Frontend |
|---------|----------|
| 401/403 admin | `RutaAdmin` redirect + toast |
| 404 | `ListState` error / toast |
| 422 URL inválida | `fieldErrors.link_info` |
| 422 campos requeridos | `fieldErrors` por campo |