# Plan de Implementación - miIFTS: Búsqueda y Filtros

## Fase: IMPLEMENTACIÓN - Búsqueda y Filtrado (Sprint Integrante 3)

### Resumen
Implementar 3 endpoints de búsqueda/filtrado siguiendo el patrón 4 capas y las decisiones D09, D10, D11.

### Orden de Ejecución

```
D09 (tipo Recurso) → RF-21 (materias) → RF-16 (recursos) → RF-20 (recordatorios) → Tests
```

D09 es prerrequisito para RF-16. RF-21 y RF-20 son independientes entre sí y de D09.

---

## Tareas

### T01 — D09: Agregar campo `tipo` al modelo Recurso
**Objective:** Agregar columna `tipo` (String, nullable=True) al modelo Recurso para habilitar filtrado por tipo de archivo. Prerrequisito para RF-16.

**Capas afectadas:** model, schema, repository
**Archivos:**
- `app/features/recursos/model.py` — agregar `tipo = Column(String, nullable=True)`
- `app/features/recursos/schema.py` — agregar `tipo: Optional[str] = None` a `RecursoBase`
- `app/features/recursos/repository.py` — actualizar `create_recurso` y `update_recurso` para incluir `tipo`

**Dependencias:** Ninguna (primer task)

**Aceptación:**
- Recurso model tiene campo `tipo` nullable
- RecursoCreate y RecursoResponse incluyen `tipo` opcional
- create/update persisten `tipo` correctamente
- Tests existentes no se rompen

**Guidance:**
- Usar `Column(String, nullable=True)` en el modelo
- Agregar `tipo: Optional[str] = None` a `RecursoBase` para que hereden Create y Response
- En repository, `create_recurso` debe pasar `tipo` al crear el objeto
- No requiere migration en desarrollo (Base.metadata.drop_all/create_all en tests)

---

### T02 — RF-21: Endpoint búsqueda de materias
**Objective:** Implementar `GET /materias/buscar` con texto libre y filtros opcionales de año/cuatrimestre.

**Capas afectadas:** schema, repository, service, router
**Archivos:**
- `app/features/materias/schema.py` — agregar `MateriaSearchQuery` (q, anio, cuatrimestre)
- `app/features/materias/repository.py` — agregar método `search(q, anio, cuatrimestre)` en `MateriaRepository`
- `app/features/materias/service.py` — agregar función `buscar_materias(db, q, anio, cuatrimestre)`
- `app/features/materias/router.py` — agregar endpoint `GET /materias/buscar`

**Dependencias:** Ninguna (independiente de D09)

**Aceptación:**
- `GET /materias/buscar?q=programacion` devuelve materias cuyo nombre o código contienen "programacion"
- `GET /materias/buscar?q=programacion&anio=1` filtra además por año
- `GET /materias/buscar?q=programacion&anio=1&cuatrimestre=1` filtra por año y cuatrimestre
- Sin resultados devuelve lista vacía `[]`
- No requiere autenticación
- FastAPI genera OpenAPI/Swagger automáticamente
- `response_model` explícito: `List[MateriaResponse]`

**Guidance:**
- El parámetro `q` es texto libre: usar `or_` con `ilike()` sobre `Materia.nombre` y `Materia.codigo`
- Filtros `anio` y `cuatrimestre` son opcionales, aplicar solo si no son None
- Usar `ilike` para búsqueda insensible a mayúsculas
- Router: no usar `Depends(get_current_user)` (no requiere auth, como otros endpoints de materias)
- Schema de query: `class MateriaSearchQuery(BaseModel)` con `Config.from_attributes = True`

---

### T03 — RF-16: Filtros avanzados para recursos
**Objective:** Extender `GET /recursos/` con filtros por materia_id, tipo, rango de fechas y ordenamiento.

**Capas afectadas:** schema, repository, service, router
**Archivos:**
- `app/features/recursos/schema.py` — agregar schema de query params (materia_id, tipo, desde, hasta)
- `app/features/recursos/repository.py` — agregar método `filter_recursos(...)` en `RecursoRepository`
- `app/features/recursos/service.py` — agregar función `get_recursos_filtrados(db, filters)` en `RecursoService`
- `app/features/recursos/routers/recursos.py` — extender `GET /` con query params opcionales

**Dependencias:** T01 (D09 requiere campo `tipo` en modelo)

**Aceptación:**
- `GET /recursos/?materia_id=1&tipo=pdf&desde=2024-01-01` funciona correctamente
- Filtros opcionales: materia_id, tipo, desde, hasta
- Ordenamiento por fecha_creacion, titulo
- Sin resultados devuelve lista vacía `[]`
- `response_model` explícito: `List[RecursoResponse]`
- FastAPI genera OpenAPI/Swagger con ejemplos

**Guidance:**
- `desde` y `hasta` son `date` query params; comparar con `func.date(Recurso.fecha_creacion)`
- En repository, construir query dinámico con SQLAlchemy, agregando filtros solo si no son None
- Ordenar por `Recurso.fecha_creacion.desc(), Recurso.titulo` por defecto
- Extender el `GET /` existente, no crear endpoint nuevo

---

### T04 — RF-20: Búsqueda de recordatorios con filtros
**Objective:** Extender `GET /recordatorios` con filtros por tipo, rango de fechas, materia_id y ordenamiento por fecha descendente.

**Capas afectadas:** schema, repository, service, router
**Archivos:**
- `app/features/recordatorios/schema.py` — agregar schema de query params (tipo, desde, hasta, materia_id)
- `app/features/recordatorios/repository.py` — agregar método `search(tipo, desde, hasta, materia_id, usuario_id)`
- `app/features/recordatorios/service.py` — agregar función `get_recordatorios_filtrados(db, usuario_id, ...)`
- `app/features/recordatorios/router.py` — extender `GET /` con query params opcionales

**Dependencias:** Ninguna (independiente)

**Aceptación:**
- `GET /recordatorios/?tipo=examen&desde=2024-12-01&hasta=2024-12-31` funciona correctamente
- Filtros opcionales: tipo, desde, hasta, materia_id
- `usuario_id` sigue siendo requerido (extender, no reemplazar)
- Ordenamiento por fecha descendente (próximos primero)
- Sin resultados devuelve lista vacía `[]`
- `response_model` explícito: `List[RecordatorioResponse]`
- FastAPI genera OpenAPI/Swagger con ejemplos

**Guidance:**
- `desde` y `hasta` son `date` query params; comparar con `func.date(Recordatorio.fecha)`
- Construir query dinámico en repository: base = `usuario_id`, agregar filtros condicionalmente
- Ordenar por `Recordatorio.fecha.desc()`
- Extender la función/service existente con params opcionales

---

### T05 — Tests para endpoints de búsqueda/filtro
**Objective:** Crear tests de validación para los 3 nuevos endpoints cubriendo casos funcionales y edge cases.

**Archivos:**
- `tests/test_recursos.py` — tests de filtrado de recursos
- `tests/test_recordatorios.py` — tests de búsqueda de recordatorios
- `tests/test_materias.py` — agregar tests de búsqueda de materias

**Dependencias:** T01, T02, T03, T04

**Aceptación:**
- Tests para búsqueda vacía (sin resultados): `[]`
- Tests para cada filtro individual y combinado
- Tests para ordenamiento (fecha descendente en recordatorios)
- Tests de edge cases: filtros sin coincidencia
- Tests existentes (test_auth.py, tests xfail en test_materias.py) no se ven afectados
- Todos los tests pasan con pytest

**Guidance:**
- Reutilizar fixtures de `conftest.py`: `client`, `db_session`, `carrera_test`
- Crear datos de test directamente en la sesión DB (Recurso, Recordatorio, Materia)
- Verificar status codes 200 y contenido de respuestas
- No modificar tests xfail existentes

---

## Flujo de Ejecución

```
[T01] D09: campo tipo en Recurso
  ↓ (prerrequisito)
[T02] RF-21: búsqueda de materias ← paraleloizable con T04
[T03] RF-16: filtros de recursos ← depende de T01
[T04] RF-20: búsqueda de recordatorios ← paraleloizable con T02
  ↓
[T05] Tests de todos los endpoints
```

T02 y T04 pueden ejecutarse en paralelo con T01 (sin dependencia). T03 depende de T01.

## Contexto de Test Data Necesario

Para los tests se necesitarán datos de prueba:
- Recursos con distintos `tipo` ("pdf", "docx", "link"), `materia_id`, `fecha_creacion`
- Recordatorios con distintos `tipo` ("parcial", "tp", "final", "examen"), `fecha`, `materia_id`
- Materias con distintos `nombre`, `codigo`, `anio`, `cuatrimestre`

Todos los datos se crean directamente en `db_session` dentro de cada test.
