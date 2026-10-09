# Materias - Contrato API

## Tipos (generados)

```typescript
// Carreras
interface CarreraCreate { nombre, duracion_cuatrimestres, ifts_id }
interface CarreraUpdate { nombre?, duracion_cuatrimestres?, ifts_id? }
interface CarreraResponse { id, nombre, duracion_cuatrimestres, ifts_id, ifts_nombre? }

// Materias
interface MateriaCreate { carrera_id, nombre, codigo, anio, cuatrimestre }
interface MateriaUpdate { nombre?, codigo?, anio?, cuatrimestre? }
interface MateriaResponse { id, carrera_id, nombre, codigo, anio, cuatrimestre, carrera_nombre? }

// Correlativas
interface CorrelativaCreate { materia_id, requiere_id }
interface CorrelativaResponse { id, materia_id, requiere_id, requiere?: MateriaResponse }

// Cursadas
interface MateriaUsuarioCreate { materia_id, cursando?, nota_parcial_1?, nota_parcial_2?, examen_final? }
interface MateriaUsuarioUpdate { cursando?, nota_parcial_1?, nota_parcial_2?, examen_final? }
interface MateriaUsuarioResponse {
  id, usuario_id, materia_id, materia_nombre, cursando,
  nota_parcial_1, nota_parcial_2, examen_final,
  nota_final: number|null,      // calculado
  estado: string                // "cursando"|"promocionada"|"aprobada"|"desaprobada"|"pendiente"
}

// Promedio
interface PromedioResponse { promedio: number|null, materias_computadas: number }

// Paginación
interface PaginatedResponse<T> { items: T[], total, page, per_page, total_pages }
```

## Endpoints Clave

### GET `/materias/buscar?q=...&anio=&cuatrimestre=&page=&per_page=`
Búsqueda texto libre (ILIKE nombre/código) + filtros opcionales año/cuatrimestre.  
Response: `PaginatedResponse<MateriaResponse>`

### GET `/materias/correlativas/{materia_id}?page=&per_page=`
Incluye `requiere` (MateriaResponse embebida) en cada item.

### GET `/materias/usuario/{usuario_id}?page=&per_page=`
Auth: propio o admin. Items incluyen `materia_nombre`, `nota_final`, `estado`.

### GET `/materias/promedio/{usuario_id}`
Auth: propio o admin. Excluye `cursando` y `pendiente`.

### POST `/materias/usuario` (auth: usuario logueado)
Body: `MateriaUsuarioCreate` (sin `usuario_id`, sale del token).  
Validaciones: usuario existe, materia existe, materia.carrera_id == usuario.carrera_id, no duplicado.

### PATCH `/materias/cursada/{id}` / DELETE `/materias/cursada/{id}`
Auth: dueño. Recalcula `nota_final` y `estado` en response.

## Cálculos Derivados (Backend → Frontend)

| Campo | Lógica |
|-------|--------|
| `nota_final` | Si `parcial1≥7 && parcial2≥7` → `round((p1+p2)/2,2)`; sino → `examen_final` |
| `estado` | `cursando` → "cursando"; promocionada → "promocionada"; `examen_final≥4` → "aprobada"; `examen_final<4` → "desaprobada"; sin examen → "pendiente" |
| `promedio` | Promedio de `nota_final` not null (excluye cursando + pendiente) |

## Errores Comunes

| Endpoint | 401 | 403 | 404 | 409 | 422 |
|----------|-----|-----|-----|-----|-----|
| POST /carreras | ✓ | ✓ | | ✓ (FK) | ✓ |
| POST /materias | ✓ | ✓ | | ✓ (código único) | ✓ |
| POST /correlativas | ✓ | ✓ | ✓ | ✓ (ciclo/duplicado) | ✓ |
| GET /usuario/{id} | ✓ | ✓ | | | ✓ |
| POST /usuario | ✓ | | | ✓ (carrera/duplicado) | ✓ |
| PATCH/DELETE /cursada/{id} | ✓ | ✓ | ✓ | | ✓ |

## Frontend Service

```typescript
// Público
catalogoService.getCarreras(params)
catalogoService.getMateriasByCarrera(carreraId, params)
catalogoService.buscarMaterias(q, anio, cuatrimestre, params)
catalogoService.getMateria(id)
catalogoService.getCorrelativas(materiaId, params)

// Auth estudiante
materiasService.getMisMaterias(usuarioId, params)
materiasService.getPromedio(usuarioId)
materiasService.agregarCursada(data)
materiasService.actualizarCursada(id, data)
materiasService.borrarCursada(id)

// Admin
adminCarrerasService.create/update/delete
adminMateriasService.create/update/delete
adminCorrelativasService.create/delete
```