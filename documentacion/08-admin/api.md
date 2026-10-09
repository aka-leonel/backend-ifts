# Admin - Contrato API

## Tipos Generados (openapi-typescript)

```typescript
// Carreras
interface CarreraCreate { nombre: string; duracion_cuatrimestres: number; ifts_id: number; }
interface CarreraUpdate { nombre?: string; duracion_cuatrimestres?: number; ifts_id?: number; }
interface CarreraResponse { id, nombre, duracion_cuatrimestres, ifts_id, ifts_nombre? }

// Materias
interface MateriaCreate { carrera_id: number; nombre: string; codigo: string; anio: number; cuatrimestre: number; }
interface MateriaUpdate { nombre?: string; codigo?: string; anio?: number; cuatrimestre?: number; }
interface MateriaResponse { id, carrera_id, nombre, codigo, anio, cuatrimestre, carrera_nombre? }

// Correlativas
interface CorrelativaCreate { materia_id: number; requiere_id: number; }
interface CorrelativaResponse { id, materia_id, requiere_id, requiere?: MateriaResponse; }

// Convenios
interface ConvenioCreate { carrera_id: number; institucion: string; carrera_destino: string; descripcion: string; link_info: string; }
interface ConvenioResponse { id, carrera_id, institucion, carrera_destino, descripcion, link_info, carrera_nombre? }

interface PaginatedResponse<T> { items: T[], total, page, per_page, total_pages }
```

## Endpoints Admin (require_admin)

### Carreras
| Método | Endpoint | Body/Params | Response |
|--------|----------|-------------|----------|
| POST | `/materias/carreras` | `CarreraCreate` | 201 `CarreraResponse` |
| PUT | `/materias/carreras/{id}` | `CarreraUpdate` | 200 `CarreraResponse` |
| DELETE | `/materias/carreras/{id}` | — | 204 |
| GET | `/materias/carreras` | `page, per_page` | `PaginatedResponse<CarreraResponse>` (público) |

### Materias
| Método | Endpoint | Body/Params | Response |
|--------|----------|-------------|----------|
| POST | `/materias/` | `MateriaCreate` | 201 `MateriaResponse` |
| PUT | `/materias/{id}` | `MateriaUpdate` | 200 `MateriaResponse` |
| DELETE | `/materias/{id}` | — | 204 |
| GET | `/materias/carrera/{carrera_id}` | `page, per_page` | `PaginatedResponse<MateriaResponse>` (público) |

### Correlativas
| Método | Endpoint | Body/Params | Response |
|--------|----------|-------------|----------|
| POST | `/materias/correlativas` | `CorrelativaCreate` | 201 `CorrelativaResponse` |
| DELETE | `/materias/correlativas/{id}` | — | 204 |
| GET | `/materias/correlativas/{materia_id}` | `page, per_page` | `PaginatedResponse<CorrelativaResponse>` (público) |

### Convenios
| Método | Endpoint | Body/Params | Response |
|--------|----------|-------------|----------|
| POST | `/convenios/` | `ConvenioCreate` | 201 `ConvenioResponse` |
| PUT | `/convenios/{id}` | `ConvenioCreate` | 200 `ConvenioResponse` |
| DELETE | `/convenios/{id}` | — | 204 |
| GET | `/convenios/` | `page, per_page` | `PaginatedResponse<ConvenioResponse>` (público) |

## Validaciones Backend Específicas Admin

| Endpoint | Validación | Error 409 |
|----------|------------|-----------|
| DELETE `/materias/carreras/{id}` | Carrera tiene materias | "No se puede eliminar una carrera con materias asociadas" |
| DELETE `/materias/{id}` | Materia tiene cursadas | "No se puede eliminar una materia con cursadas asociadas" |
| POST `/materias/` | Código único por carrera | "Ya existe una materia con código 'X' en esa carrera" |
| POST `/materias/correlativas` | Genera ciclo (DFS detecta camino `requiere_id` → `materia_id`) | "Esa correlativa generaría un ciclo..." |
| POST `/materias/correlativas` | Correlativa ya existe | "Esa correlativa ya existe" |

## Ejemplos

### Crear Carrera (Admin)
```bash
POST /materias/carreras
Authorization: Bearer <admin_token>
{ "nombre": "Tecnicatura en Data Science", "duracion_cuatrimestres": 6, "ifts_id": 1 }
```

### Crear Materia (Admin)
```bash
POST /materias/
Authorization: Bearer <admin_token>
{ "carrera_id": 1, "nombre": "Machine Learning", "codigo": "ML201", "anio": 2, "cuatrimestre": 1 }
```

### Crear Correlativa - Ciclo Detectado
```bash
POST /materias/correlativas
Authorization: Bearer <admin_token>
{ "materia_id": 5, "requiere_id": 3 }
```
**409 si 3 → ... → 5 ya existe:**
```json
{ "detail": "Esa correlativa generaría un ciclo: la materia requerida ya depende, directa o indirectamente, de esta materia" }
```

### Crear Convenio (Admin)
```bash
POST /convenios/
Authorization: Bearer <admin_token>
{ "carrera_id": 1, "institucion": "UNLP", "carrera_destino": "Lic. Cs. Computación", "descripcion": "Articulación...", "link_info": "https://unlp.edu.ar/..." }
```

## Códigos Error Admin

| Endpoint | 401 | 403 | 404 | 409 | 422 |
|----------|-----|-----|-----|-----|-----|
| POST /materias/carreras | ✓ | ✓ | | ✓ (FK) | ✓ |
| PUT/DELETE /materias/carreras/{id} | ✓ | ✓ | ✓ | ✓ (tiene materias) | ✓ |
| POST /materias/ | ✓ | ✓ | | ✓ (código único) | ✓ |
| PUT/DELETE /materias/{id} | ✓ | ✓ | ✓ | ✓ (tiene cursadas) | ✓ |
| POST /materias/correlativas | ✓ | ✓ | ✓ | ✓ (ciclo/duplicado) | ✓ |
| DELETE /materias/correlativas/{id} | ✓ | ✓ | ✓ | | |
| POST /convenios/ | ✓ | ✓ | | | ✓ |
| PUT/DELETE /convenios/{id} | ✓ | ✓ | ✓ | | ✓ |

## Frontend Services (Admin)

```typescript
// features/catalogo-admin/service.ts
adminCarrerasService.getAll(params)
adminCarrerasService.create(data)
adminCarrerasService.update(id, data)
adminCarrerasService.delete(id)

adminMateriasService.getAll(params)  // con filtros carrera, anio, cuatrimestre
adminMateriasService.create(data)
adminMateriasService.update(id, data)
adminMateriasService.delete(id)

adminCorrelativasService.getByMateria(materiaId, params)
adminCorrelativasService.create(data)
adminCorrelativasService.delete(id)

// features/convenios-admin/service.ts
adminConveniosService.getAll(params)
adminConveniosService.create(data)
adminConveniosService.update(id, data)
adminConveniosService.delete(id)
```