# Admin - Frontend

## Pantalla `/admin` (solo `rol === "admin"`)

### Guard y Nav Dinámico

- `RutaAdmin` verifica `usuario.rol === "admin"` → sino redirect `/` (o `/login` si no autenticado)
- `SidebarNav` / `BottomNav`:
  - **Admin:** `[Admin, Perfil]` (REEMPLAZA nav estudiante - D019)
  - **Estudiante:** `[Inicio, Mis Materias, Recordatorios, Recursos, Convenios, Perfil]`
- Login admin → `navigate("/admin")` directo (aterriza en panel)

### AdminScreen (`features/admin/AdminScreen.tsx`)

- **Tabs principales:** Catálogo / Convenios
- **Catálogo → Sub-tabs:** Carreras / Materias / Correlativas

---

## Catálogo Admin (`features/catalogo-admin/`)

### Carreras Admin (`CarrerasAdmin.tsx`)
- Lista paginada + `ListState` + `Paginador`
- FAB "Crear" → `FormModal` + `carreraAdminSpec`
- Actions: Editar (PUT), Borrar (DELETE + `ConfirmDialog`)
- Validación 409: "No se puede eliminar carrera con materias"

### Materias Admin (`MateriasAdmin.tsx`)
- Lista con filtros (carrera, año, cuatrimestre) + FAB "Crear"
- `materiaAdminSpec`: select carrera, nombre, código, año, cuatrimestre
- Validación 409: código único por carrera
- Actions: Editar, Borrar (409 si tiene cursadas)

### Correlativas Admin (`CorrelativasAdmin.tsx`)
- Lista existentes (con `requiere` embebido)
- FAB "Agregar" → `FormModal` + `correlativaAdminSpec`
- **2 Selects** con misma lista materias: `materia_id` / `requiere_id`
- Validación cliente: `requiere_id !== materia_id`
- Backend valida ciclos reales (DFS) → 409 toast "Generaría un ciclo"

---

## Convenios Admin (`features/convenios-admin/`)

- CRUD completo convenios
- `convenioAdminSpec`: select carrera, institución, carrera_destino, textarea descripción, url link_info
- Lista paginada + FAB crear + editar/borrar
- Validación: `link_info` tipo URL

---

## Specs Admin

```typescript
carreraAdminSpec = [
  { name: "nombre", label: "Nombre", type: "text", required: true },
  { name: "duracion_cuatrimestres", label: "Duración (cuatrimestres)", type: "number", required: true, min: 1, max: 10 },
  { name: "ifts_id", label: "IFTS", type: "select", required: true, options: [], optionLabel: "nombre", optionValue: "id" }
]

materiaAdminSpec = [
  { name: "carrera_id", label: "Carrera", type: "select", required: true, options: [], optionLabel: "nombre", optionValue: "id" },
  { name: "nombre", label: "Nombre", type: "text", required: true },
  { name: "codigo", label: "Código", type: "text", required: true, maxLength: 20 },
  { name: "anio", label: "Año", type: "number", required: true, min: 1, max: 5 },
  { name: "cuatrimestre", label: "Cuatrimestre", type: "number", required: true, min: 1, max: 2 }
]

correlativaAdminSpec = [
  { name: "materia_id", label: "Materia", type: "select", required: true, options: [], optionLabel: "nombre", optionValue: "id" },
  { name: "requiere_id", label: "Requiere (Correlativa)", type: "select", required: true, options: [], optionLabel: "nombre", optionValue: "id" }
  // Validación cliente: requiere_id !== materia_id
]

convenioAdminSpec = [
  { name: "carrera_id", label: "Carrera", type: "select", required: true, options: [], optionLabel: "nombre", optionValue: "id" },
  { name: "institucion", label: "Institución", type: "text", required: true, maxLength: 150 },
  { name: "carrera_destino", label: "Carrera Destino", type: "text", required: true, maxLength: 150 },
  { name: "descripcion", label: "Descripción", type: "textarea", required: true, rows: 4 },
  { name: "link_info", label: "Link Información", type: "url", required: true }
]
```

---

## Tipos Generados (`npm run gen:api`)

```typescript
// src/api/schema.d.ts (desde openapi.json backend)
CarreraCreate, CarreraUpdate, MateriaCreate, MateriaUpdate, CorrelativaCreate, ConvenioCreate
```
Admin importa tipos generados (single source of truth).

---

## Components Compartidos

| Componente | Uso |
|------------|-----|
| `Tabs` / `TabsList` / `TabsTrigger` / `TabsContent` | AdminShell tabs + sub-tabs |
| `FormModal` + `EntityForm` + `*AdminSpec` | Create/Edit todas entidades admin |
| `ListState` + `Paginador` | Listas paginadas admin |
| `ConfirmDialog` | Delete confirmations |
| `Select` opciones dinámicas | FK selects (carrera, IFTS, materia) |
| `Toaster` | Feedback |