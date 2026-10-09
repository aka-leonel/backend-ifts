# Convenios + TalentoTech - Contrato API

## Tipos

```typescript
// Convenio
interface ConvenioCreate {
  carrera_id: number;
  institucion: string;        // max 150
  carrera_destino: string;    // max 150
  descripcion: string;
  link_info: string;          // HttpUrl
}
interface ConvenioResponse {
  id, carrera_id, institucion, carrera_destino, descripcion, link_info, carrera_nombre?
}

// TalentoTech
interface TalentoTechCreate {
  carrera_id: number;
  nombre_curso: string;       // max 150
  categoria: string;          // max 20
  descripcion: string;
  duracion: string;           // max 50
  link_inscripcion: string;   // HttpUrl
}
interface TalentoTechResponse {
  id, carrera_id, nombre_curso, categoria, descripcion, duracion, link_inscripcion, carrera_nombre?
}

interface PaginatedResponse<T> { items: T[], total, page, per_page, total_pages }
```

## Endpoints Convenios

| Método | Ruta | Auth | Body/Params | Response |
|--------|------|------|-------------|----------|
| GET | `/convenios/` | ❌ | `page, per_page` | `PaginatedResponse<ConvenioResponse>` |
| GET | `/convenios/carrera/{id}` | ❌ | `page, per_page` | `PaginatedResponse<ConvenioResponse>` |
| GET | `/convenios/{id}` | ❌ | — | `ConvenioResponse` |
| POST | `/convenios/` | ✅ Admin | `ConvenioCreate` | 201 `ConvenioResponse` |
| PUT | `/convenios/{id}` | ✅ Admin | `ConvenioCreate` | 200 `ConvenioResponse` |
| DELETE | `/convenios/{id}` | ✅ Admin | — | 204 |

## Endpoints TalentoTech

| Método | Ruta | Auth | Body/Params | Response |
|--------|------|------|-------------|----------|
| GET | `/talentotech/` | ❌ | `page, per_page` | `PaginatedResponse<TalentoTechResponse>` |
| GET | `/talentotech/carrera/{id}` | ❌ | `page, per_page` | `PaginatedResponse<TalentoTechResponse>` |
| GET | `/talentotech/categoria/{cat}` | ❌ | `page, per_page` (exact match) | `PaginatedResponse<TalentoTechResponse>` |
| GET | `/talentotech/{id}` | ❌ | — | `TalentoTechResponse` |
| POST | `/talentotech/` | ✅ Admin | `TalentoTechCreate` | 201 `TalentoTechResponse` |
| PUT | `/talentotech/{id}` | ✅ Admin | `TalentoTechCreate` | 200 `TalentoTechResponse` |
| DELETE | `/talentotech/{id}` | ✅ Admin | — | 204 |

## Ejemplos

### Crear Convenio (Admin)
```bash
POST /convenios/
Authorization: Bearer <admin_token>
{ "carrera_id": 1, "institucion": "UNLP", "carrera_destino": "Lic. Cs. Computación", "descripcion": "Articulación...", "link_info": "https://unlp.edu.ar/..." }
```

### Crear TalentoTech (Admin)
```bash
POST /talentotech/
Authorization: Bearer <admin_token>
{ "carrera_id": 1, "nombre_curso": "Desarrollo Web Full Stack", "categoria": "Programación", "descripcion": "Curso intensivo...", "duracion": "3 meses", "link_inscripcion": "https://talentotech.ar/..." }
```

### Filtrar TalentoTech por Categoría
```bash
GET /talentotech/categoria/Programaci%C3%B3n?page=1&per_page=10
```

## Códigos Error

| Endpoint | 401 | 403 | 404 | 422 |
|----------|-----|-----|-----|-----|
| GET convenios/ | | | | ✓ |
| POST convenios/ | ✓ | ✓ | | ✓ |
| PUT/DELETE convenios/{id} | ✓ | ✓ | ✓ | ✓ |
| GET talentotech/ | | | | ✓ |
| POST talentotech/ | ✓ | ✓ | | ✓ |
| PUT/DELETE talentotech/{id} | ✓ | ✓ | ✓ | ✓ |

## Frontend Services

```typescript
// Público (features/convenios/service.ts)
conveniosService.getAll(params)
conveniosService.getByCarrera(carreraId, params)
conveniosService.getById(id)
talentotechService.getAll(params)
talentotechService.getByCarrera(carreraId, params)
talentotechService.getByCategoria(categoria, params)
talentotechService.getById(id)

// Admin (features/convenios-admin/service.ts)
adminConveniosService.getAll(params)
adminConveniosService.create(data)
adminConveniosService.update(id, data)
adminConveniosService.delete(id)
```