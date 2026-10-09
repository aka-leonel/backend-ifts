# Recursos - Contrato API

## Tipos

```typescript
interface RecursoCreate {
  titulo: string;           // max 150
  url: string;              // HttpUrl
  descripcion: string;
  tipo?: string;            // pdf, video, link, documento, otro
  materia_id: number;
}

interface RecursoResponse {
  id: number;
  usuario_id: number;
  materia_id: number;
  titulo: string;
  url: string;
  descripcion: string;
  tipo: string | null;
  fecha_creacion: string;   // ISO 8601
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
```

## Endpoints

### GET `/recursos/?materia_id&tipo&desde&hasta&page&per_page`
Lista global con filtros opcionales. Orden: `fecha_creacion DESC`.  
Response: `PaginatedResponse<RecursoResponse>`

### GET `/recursos/{id}`
Detalle. Response: `RecursoResponse` (404 si no existe)

### POST `/recursos/` (Auth: usuario)
Body: `RecursoCreate` → Response 201 `RecursoResponse` (usuario_id del token, fecha_creacion server)

### PUT `/recursos/{id}` (Auth: dueño)
Body: `RecursoCreate` (reemplazo completo) → Response 200 `RecursoResponse` (403 si ajeno, 404 si no existe)

### DELETE `/recursos/{id}` (Auth: dueño)
Response 204 (403 si ajeno, 404 si no existe)

### GET `/recursos/usuario/{usuario_id}?page&per_page`
Por usuario. Orden: `fecha_creacion DESC`. Response: `PaginatedResponse<RecursoResponse>`

### GET `/recursos/materia/{materia_id}?page&per_page`
Por materia. Orden: `fecha_creacion DESC`. Response: `PaginatedResponse<RecursoResponse>`

## Ejemplos

### Crear
```bash
POST /recursos/
Authorization: Bearer <token>
{ "titulo": "Apuntes Algoritmos", "url": "https://drive.google.com/...", "descripcion": "Resumen...", "tipo": "pdf", "materia_id": 5 }
```

### Filtrar
```bash
GET /recursos/?materia_id=5&tipo=pdf&desde=2024-01-01&hasta=2024-12-31&page=1&per_page=10
```

## Códigos Error

| Endpoint | 401 | 403 | 404 | 422 |
|----------|-----|-----|-----|-----|
| GET /recursos/ | | | | ✓ |
| GET /recursos/{id} | | | ✓ | ✓ |
| POST /recursos/ | ✓ | | | ✓ |
| PUT /recursos/{id} | ✓ | ✓ | ✓ | ✓ |
| DELETE /recursos/{id} | ✓ | ✓ | ✓ | |
| GET /usuario/{id} | | | | ✓ |
| GET /materia/{id} | | | | ✓ |

## Frontend Service

```typescript
recursosService.getAll(params, filters)
recursosService.getById(id)
recursosService.getByUsuario(usuarioId, params)
recursosService.getByMateria(materiaId, params)
recursosService.create(data)
recursosService.update(id, data)
recursosService.delete(id)
```