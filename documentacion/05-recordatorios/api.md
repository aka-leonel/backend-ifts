# Recordatorios - Contrato API

## Tipos

```typescript
interface RecordatorioCreate {
  titulo: string;           // max 100
  fecha: string;            // ISO 8601
  tipo: string;             // "parcial" | "tp" | "final" | "otro"
  materia_id?: number;
}

interface RecordatorioUpdate {
  titulo?: string;
  fecha?: string;
  tipo?: string;
  materia_id?: number;
}

interface RecordatorioResponse {
  id: number;
  titulo: string;
  fecha: string;            // ISO 8601
  tipo: string;
  usuario_id: number;
  materia_id: number | null;
  materia_nombre?: string;  // calculado en service si join
}

interface PaginatedResponse<T> { items: T[], total, page, per_page, total_pages }
```

## Endpoints

### GET `/recordatorios/?tipo&desde&hasta&materia_id&page&per_page`
Lista usuario autenticado. Orden: `fecha DESC`.  
Response: `PaginatedResponse<RecordatorioResponse>`

### POST `/recordatorios/` (Auth: usuario)
Body: `RecordatorioCreate` → 201 `RecordatorioResponse` (usuario_id del token)

### PATCH `/recordatorios/{id}` (Auth: dueño)
Body: `RecordatorioUpdate` (parcial) → 200 `RecordatorioResponse` (404 si no existe o no es dueño)

### DELETE `/recordatorios/{id}` (Auth: dueño)
204 (404 si no existe o no es dueño)

## Ejemplos

### Crear
```bash
POST /recordatorios/
Authorization: Bearer <token>
{ "titulo": "Parcial Algoritmos", "fecha": "2024-04-15T18:00:00", "tipo": "parcial", "materia_id": 5 }
```

### Filtrar
```bash
GET /recordatorios/?tipo=parcial&desde=2024-04-01&hasta=2024-04-30&materia_id=5&page=1&per_page=10
```

### Actualizar
```bash
PATCH /recordatorios/12
Authorization: Bearer <token>
{ "fecha": "2024-04-16T18:00:00", "tipo": "final" }
```

## Códigos Error

| Endpoint | 401 | 404 | 422 |
|----------|-----|-----|-----|
| GET /recordatorios/ | ✓ | | ✓ |
| POST /recordatorios/ | ✓ | | ✓ |
| PATCH /recordatorios/{id} | ✓ | ✓ | ✓ |
| DELETE /recordatorios/{id} | ✓ | ✓ | |

## Frontend Service

```typescript
recordatoriosService.getAll(params, filters)
recordatoriosService.create(data)
recordatoriosService.update(id, data)
recordatoriosService.delete(id)
```