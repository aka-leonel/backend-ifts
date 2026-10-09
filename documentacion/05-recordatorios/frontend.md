# Recordatorios - Frontend

## Pantalla

| Pantalla | Ruta | Descripción |
|----------|------|-------------|
| Agenda Global | `/recordatorios` | Lista agrupada "Esta semana" / "Más adelante", FAB crear, filtros, cards edit/delete |

---

## Servicio (`features/recordatorios/service.ts`)

```typescript
recordatoriosService.getAll(params, filters?)     // GET /recordatorios/ con query params
recordatoriosService.create(data)                  // POST /recordatorios/
recordatoriosService.update(id, data)              // PATCH /recordatorios/{id}
recordatoriosService.delete(id)                    // DELETE /recordatorios/{id}
```

## Hooks (`hooks.ts`)

- `useRecordatorios(params, filters)` → `useAsyncQuery`
- `useCrearRecordatorio()` / `useActualizarRecordatorio(id)` / `useBorrarRecordatorio()` → `useApiForm`

## Spec (`recordatorioSpec.ts`)

```typescript
recordatorioSpec = [
  { name: "titulo", label: "Título", type: "text", required: true, maxLength: 100 },
  { name: "fecha", label: "Fecha y hora", type: "datetime-local", required: true },
  { name: "tipo", label: "Tipo", type: "select", required: true,
    options: [{v:"parcial",l:"Parcial"}, {v:"tp",l:"Trabajo Práctico"}, {v:"final",l:"Final"}, {v:"otro",l:"Otro"}] },
  { name: "materia_id", label: "Materia (opcional)", type: "select", required: false,
    options: [], placeholder: "Sin materia asociada" } // se carga: materias cursadas + "Sin materia"
]
```

## Pantalla (`RecordatoriosScreen.tsx`)

### Agrupación Visual (cliente)
```typescript
const ahora = new Date(); const finSemana = new Date(); finSemana.setDate(ahora.getDate() + 7);
const estaSemana = items.filter(r => new Date(r.fecha) <= finSemana);
const masAdelante = items.filter(r => new Date(r.fecha) > finSemana);
```

### Estructura
- **Toolbar filtros:** Select Tipo, DateRangePicker (desde/hasta), Select Materia, Botón Limpiar
- **Sección "Esta semana"** (≤ 7 días): `RecordatorioCard` grid
- **Sección "Más adelante"** (> 7 días): `RecordatorioCard` grid
- **EmptyState:** "No hay recordatorios" + botón "Crear primero"
- **FAB:** Abre `FormModal` create (fecha default = ahora + 1h, tipo = "otro")

## Card (`RecordatorioCard.tsx`)

- Barra lateral colorida por tipo: parcial=azul, tp=verde, final=rojo, otro=gris
- `TipoBadge` chip, título, `MateriaChip` (si aplica), fecha formateada
- Botones: Editar (abre `FormModal` prefill), Eliminar (`ConfirmDialog`)

## Push Notifications Integration

- `RecordatoriosScreen` mount → `usePush.subscribe()` si `permission === "granted"`
- Ver `06-push/frontend.md` para detalles completos

## Validaciones Cliente

| Campo | Regla |
|-------|-------|
| `titulo` | Required, max 100 |
| `fecha` | Required, datetime-local (futura validada en submit) |
| `tipo` | Required, select 4 opciones |
| `materia_id` | Select opcional (materias cursadas + "Sin materia") |

## Errores

| Backend | Frontend |
|---------|----------|
| 401 | `apiClient` → logout + redirect login |
| 404 update/delete | Toast "No encontrado" |
| 422 fecha/tipo | `fieldErrors.fecha` / `fieldErrors.tipo` |
| 422 FK | `fieldErrors.materia_id` |

## Components Compartidos

`FormModal` + `EntityForm` + `recordatorioSpec`, `ListState`, `Paginador`, `FilterToolbar`, `RecordatorioCard`, `TipoBadge`, `MateriaChip`, `ConfirmDialog`, `FAB`, `Toaster`