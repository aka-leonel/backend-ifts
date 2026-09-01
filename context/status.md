# Estado Operativo del Proyecto miIFTS

## Fase: IMPLEMENTACIÓN - BÚSQUEDA Y FILTRADO
- Backend con 4 features funcionales + 3 nuevos endpoints de búsqueda/filtrado en desarrollo.
- Tests con pytest configurados (22 tests totales: 20 activos + 2 xfail).
- Sprint planificado en `TAREAS_SPRINT.md`.

## Items por Feature
| Feature | Endpoints | Capas | Estado |
|---------|-----------|-------|--------|
| auth | 4 | 6 (model, schema, repo, service, router, deps) | ✅ Completo |
| materias | 15 + 1 nuevo | 5 (model, schema, repo, service, router) | 🔧 Buscar en desarrollo |
| recordatorios | 3 + búsqueda | 5 (model, schema, repo, service, router) | 🔧 Búsqueda en desarrollo |
| recursos | 10 + filtrado | 6 (model, schema, repo, service, router, deps) | 🔧 Filtrado en desarrollo (D09: campo `tipo`) |

## Nuevos Endpoints en Desarrollo
| Endpoint | Feature | Estado |
|----------|---------|--------|
| `GET /materias/buscar` | RF-21 | 🔧 Planificado |
| `GET /recursos/?materia_id=&tipo=&desde=&hasta=` | RF-16 | 🔧 Planificado (depende D09) |
| `GET /recordatorios/?tipo=&desde=&hasta=&materia_id=` | RF-20 | 🔧 Planificado |

## Testing
| Archivo | Tests | Estado |
|---------|-------|--------|
| tests/test_auth.py | 6 | ✅ Pasan |
| tests/test_materias.py | 14 + 2 xfail | ⚠️ xfail documentados |
| tests/test_recursos.py | - | 🔙 Por crear |
| tests/test_recordatorios.py | - | 🔙 Por crear |

## Decisiones Clave en Implementación
- **D09**: Campo `tipo` agregado a model Recurso (String, nullable=True) — prerrequisito para RF-16
- **D10**: Nuevo endpoint `GET /materias/buscar` con query params `q`, `anio`, `cuatrimestre`
- **D11**: Extender `GET /recordatorios` con query params opcionales `tipo`, `desde`, `hasta`, `materia_id`

## Configuración Requerida
- `.env` con `DATABASE_URL` y `SECRET_KEY` (no presente en repo).
- Valores por defecto disponibles en `app/database.py` y `app/features/auth/service.py`.

## Riesgos Conocidos
- `get_usuario_actual()` hardcodea `1` en `materias/router.py`.
- `MateriaRepository.create()` no atrapa `IntegrityError` (falla 500 en vez de 409).
- Sin `.env` el servidor usa valores por defecto (secret débil, SQLite local).
- Tests para recursos y recordatorios no existentes aún.
- Roles admin/estudiante sin control de acceso por endpoint.
- El modelo Recurso no tenía campo `tipo` — D09 lo agrega.
- El repository de recordatorios solo tenía `get_by_usuario` — necesita nuevo método dinámico.
- El repository de materias no tenía método de búsqueda por texto libre.

## Siguiente Acción
Ejecutar T01 (D09: campo tipo en Recurso) → T02/T03/T04 (endpoints) → T05 (tests).
