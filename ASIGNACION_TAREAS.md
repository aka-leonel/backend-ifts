# Asignación de Tareas - Sprint 4 días

## 🎯 Resumen Ejecutivo

| Integrante | Tarea Principal | Prioridad | Archivos a modificar |
|------------|----------------|-----------|---------------------|
| **1** | Seguridad + JWT en CRUD | 🔴 ALTA | `materias/router.py`, `recursos/router.py` |
| **2** | Tests + CI/CD | 🔴 ALTA | `tests/`, `.github/workflows/` |
| **3** | Búsqueda y Filtros | 🟡 MEDIA | `materias/service.py`, `recursos/service.py` |
| **4** | Paginación | 🟡 MEDIA | `schemas/pagination.py`, todos los routers |
| **5** | Validaciones | 🔴 ALTA | `*/schema.py`, `exceptions.py` |

---

## 📋 Integrante 1 - Seguridad (CRÍTICO)

### ¿Qué hacer?
Proteger todos los endpoints CRUD con autenticación JWT

### Checklist:
```python
# materias/router.py
from app.features.auth.dependencies import get_current_user
from app.features.auth.schema import UsuarioResponse

# En CADA endpoint de CREATE, UPDATE, DELETE:
def crear_carrera(
    datos: CarreraCreate,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioResponse = Depends(get_current_user)  # ← AGREGAR ESTO
):
    # ...
```

### Archivos a modificar:
- `app/features/materias/router.py` (6 endpoints)
- `app/features/recursos/router.py` (si tiene PUT/DELETE)
- `app/features/recordatorios/router.py` (todos)

### Tiempo estimado: 2-3 días

---

## 🧪 Integrante 2 - Tests (CRÍTICO)

### ¿Qué hacer?
Escribir tests para asegurar que todo funciona

### Crear estos archivos:
```
tests/
  __init__.py
  conftest.py          # ← Fixtures compartidos
  test_auth.py         # ← 6 tests
  test_materias.py     # ← 6 tests
  test_recursos.py     # ← 3 tests
```

### Ejemplo de test:
```python
def test_crear_carrera_sin_auth(client):
    response = client.post("/materias/carreras", json={
        "nombre": "Test",
        "duracion_cuatrimestres": 5,
        "ifts_id": 1
    })
    assert response.status_code == 401
```

### Tiempo estimado: 3-4 días

---

## 🔍 Integrante 3 - Búsqueda

### ¿Qué hacer?
Agregar endpoints para buscar/filtrar datos

### Nuevos endpoints:
```python
# materias/router.py
@router.get("/buscar")
def buscar_materias(
    q: str = None,           # Búsqueda por nombre/código
    anio: int = None,
    cuatrimestre: int = None,
    db: Session = Depends(get_db)
):
    return service.buscar_materias(db, q, anio, cuatrimestre)
```

### Archivos:
- `materias/router.py` + `service.py` + `repository.py`
- `recursos/router.py` + `service.py`
- `recordatorios/router.py` + `service.py`

### Tiempo estimado: 3 días

---

## 📄 Integrante 4 - Paginación

### ¿Qué hacer?
Hacer que los listados no devuelvan miles de resultados

### Crear esquema compartido:
```python
# app/schemas/pagination.py
from pydantic import BaseModel
from typing import List, Generic, TypeVar

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int
```

### Modificar endpoints:
```python
@router.get("/", response_model=PaginatedResponse[MateriaResponse])
def listar_materias(
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db)
):
    # ...
```

### Tiempo estimado: 2-3 días

---

## 📝 Integrante 5 - Validaciones (CRÍTICO)

### ¿Qué hacer?
Asegurar que los datos sean válidos antes de guardarlos

### Agregar validadores:
```python
# materias/schema.py
from pydantic import validator

class MateriaCreate(BaseModel):
    codigo: str
    cuatrimestre: int
    
    @validator('codigo')
    def codigo_uppercase(cls, v):
        return v.upper()
    
    @validator('cuatrimestre')
    def cuatrimestre_valido(cls, v):
        if v not in [1, 2]:
            raise ValueError('Cuatrimestre debe ser 1 o 2')
        return v
```

### Crear excepciones custom:
```python
# app/exceptions.py
from fastapi import HTTPException

class NotFoundError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=404, detail=detail)

class DuplicateError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=409, detail=detail)
```

### Tiempo estimado: 3 días

---

## 🗓️ Plan Día a Día

### Día 1
- [ ] Todos: Git pull, crear rama feature
- [ ] Int 1: Proteger 3 endpoints de materias
- [ ] Int 2: Setup tests + 3 tests de auth
- [ ] Int 3: Endpoint búsqueda materias
- [ ] Int 4: Crear schema paginación
- [ ] Int 5: Validadores de materias

### Día 2
- [ ] Int 1: Proteger otros 3 endpoints
- [ ] Int 2: 6 tests de materias
- [ ] Int 3: Filtros de recursos
- [ ] Int 4: Paginación en 2 endpoints
- [ ] Int 5: Crear exceptions.py

### Día 3
- [ ] Int 1: Proteger recordatorios
- [ ] Int 2: Tests recursos + CI
- [ ] Int 3: Filtros recordatorios
- [ ] Int 4: Paginación en 1 endpoint más
- [ ] Int 5: Validaciones lógica negocio

### Día 4
- [ ] Todos: Testing cruzado
- [ ] Todos: Crear PRs
- [ ] Todos: Code review
- [ ] Merge a dev si todo OK

---

## ✅ Definición de "Hecho"

Una tarea está terminada cuando:
- [ ] El código funciona localmente
- [ ] Está pusheado a tu rama feature
- [ ] Está documentado (docstrings, comentarios)
- [ ] Actualizado api-requests.http si agregaste endpoints
- [ ] PR creado en GitHub

---

## 🆘 Si te trabas

1. **Pregunta en el grupo** - Alguien ya lo hizo
2. **Lee TESTING.md** - Tiene ejemplos
3. **Revisa el código existente** - Busca patrones similares
4. **Googlea el error** - Copia el mensaje exacto

---

## 📊 Al final del sprint

Completar esta tabla:

| ¿Qué completaste? | ¿Qué faltó? | ¿Qué aprendiste? |
|-------------------|-------------|------------------|
|                   |             |                  |

---

**Ver detalles completos en:** `TAREAS_SPRINT.md`
