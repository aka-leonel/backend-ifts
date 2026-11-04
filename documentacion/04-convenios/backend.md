# Convenios + TalentoTech — Backend

> Última actualización: 2026-11-04.
> Código: `app/features/recursos/{model,schema,repository,service}.py`,
> `app/features/recursos/routers/{convenios,talentotech}.py`.

---

## 1. Endpoints

### 1.1 Convenios (`/convenios`)

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/convenios/` | Pública | Lista paginada; `?q=` busca en institución/destino/descripción |
| GET | `/convenios/carrera/{carrera_id}` | Pública | Explícitos de la carrera + wildcard; acepta `?q=` |
| GET | `/convenios/{id}` | Pública | Detalle |
| POST | `/convenios/` | Admin | Crea (`ConvenioCreate`) |
| PUT | `/convenios/{id}` | Admin | Reemplazo total (`ConvenioCreate`) |
| PATCH | `/convenios/{id}` | Admin | Edición parcial (`ConvenioUpdate`) |
| DELETE | `/convenios/{id}` | Admin | Elimina (204) |

### 1.2 TalentoTech (`/talentotech`)

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/talentotech/` | Pública | Lista paginada, orden alfabético por curso |
| GET | `/talentotech/carrera/{carrera_id}` | Pública | Explícitos de la carrera + wildcard |
| GET | `/talentotech/categoria/{categoria}` | Pública | Por categoría (igualdad exacta) |
| GET | `/talentotech/{id}` | Pública | Detalle |
| POST | `/talentotech/` | Admin | Crea (`TalentoTechCreate`) |
| PUT | `/talentotech/{id}` | Admin | Reemplazo total (`TalentoTechCreate`) |
| DELETE | `/talentotech/{id}` | Admin | Elimina (204) |

> No existe `PATCH` para TalentoTech.

---

## 2. Modelos

```python
# Convenio
__table_args__ = UniqueConstraint(
    "institucion", "carrera_destino", name="uq_convenios_institucion_destino"
)
id, institucion(150), carrera_destino(150), descripcion(Text), link_info(Text),
todas_las_carreras(Boolean, default False)

# ConvenioCarrera  (tabla intermedia N:M)
convenio_id  FK convenios.id  ON DELETE CASCADE  PK
carrera_id   FK carreras.id                      PK

# TalentoTech
__table_args__ = UniqueConstraint(
    "institucion", "nombre_curso", name="uq_talentotech_institucion_curso"
)
id, institucion(150), nombre_curso(150), categoria(20), descripcion(Text),
duracion(50), modalidad_cursada(50), dificultad(30, nullable),
link_inscripcion(Text), todas_las_carreras(Boolean, default False)

# TalentoTechCarrera  (tabla intermedia N:M)
talentotech_id  FK talentotech.id  ON DELETE CASCADE  PK
carrera_id      FK carreras.id                        PK
```

- `carreras` es una relación `secondary` con `lazy="selectin"` y
  `order_by="Carrera.nombre"` ⇒ la respuesta sale ordenada por nombre.
- Ninguna tabla tiene `created_at` / `updated_at`.
- `todas_las_carreras = true` **no** genera filas en la tabla intermedia.

### 2.1 Migraciones

| Revisión | Contenido |
|---|---|
| `b7d2f8c41a30` | Unicidad `(institucion, carrera_destino)` en convenios |
| `d4f6a1c9e2b7` | Convenios: `convenios_carreras` + `todas_las_carreras`; dropea `carrera_id` |
| `e8b3c1d5f7a9` | TalentoTech: `talentotech_carreras` + `todas_las_carreras` + `institucion`/`modalidad_cursada`/`dificultad`; dropea `carrera_id` |

Ambas migraciones N:M son manuales (sin autogenerate) y soportan SQLite (batch)
y PostgreSQL.

---

## 3. Repositorios

### 3.1 `_CarreraLookupMixin`

Compartido por ambos repositorios:

- `carreras_existentes(ids) -> set[int]`: valida todos los ids en una consulta.
- `get_carreras(ids) -> list[Carrera]`: devuelve en el orden recibido.

### 3.2 `ConvenioRepository`

| Método | Comportamiento |
|---|---|
| `query_all(q)` | Orden `lower(institucion), id`; aplica `q` (ILIKE en 3 campos) |
| `query_by_carrera(id, q)` | Si la carrera no existe → vacío. Si existe → `todas_las_carreras = true` **OR** `carreras.any(id)` (EXISTS, sin duplicar) + `q` + orden |
| `get_by_unique_key(institucion, carrera_destino, exclude_id)` | Detección de duplicados |
| `create_convenio(data, carreras)` | Persiste campos + asociaciones |
| `update_convenio(id, data, carreras)` | Reemplazo total |
| `update_convenio_parcial(id, datos, carreras)` | Aplica solo las claves presentes (`carreras=None` conserva) |
| `delete_convenio(id)` | Borra el convenio y sus asociaciones |

### 3.3 `TalentoTechRepository`

| Método | Comportamiento |
|---|---|
| `query_all()` | Orden `lower(nombre_curso), id` |
| `query_by_carrera(id)` | Si la carrera no existe → vacío; si existe → wildcard **OR** `carreras.any(id)` |
| `query_by_categoria(categoria)` | Igualdad exacta + orden |
| `get_by_unique_key(institucion, nombre_curso, exclude_id)` | Duplicados |
| `create_talentotech(data, carreras)` | Persiste todos los campos + asociaciones |
| `update_talentotech(id, data, carreras)` | Reemplazo total (incluye carreras) |
| `delete_talentotech(id)` | Borra curso y asociaciones |

---

## 4. Servicios

### 4.1 Helpers compartidos (módulo)

- `_validar_carreras(repository, carrera_ids)`:
  deduplica preservando orden y valida existencia; lanza
  `DomainValidationError` con los ids faltantes.
- `_resolver_conjunto(repository, carrera_ids, todas_las_carreras)`:
  aplica la invariante flag ↔ ids y devuelve los ids finales.

### 4.2 `ConvenioService`

| Método | Comportamiento |
|---|---|
| `get_all_paginado(params, q)` | `paginate(query_all(q))` |
| `get_by_carrera_paginado(id, params, q)` | `paginate(query_by_carrera(id, q))` |
| `get_by_id(id)` | `404` → `No se encontró el convenio {id}` |
| `create(data)` | Resuelve carreras → valida unicidad → persiste |
| `update(id, data)` | Igual que create, con `exclude_id` en unicidad |
| `update_parcial(id, data)` | `PATCH`: combina con el estado actual; valida colisión de clave; maneja wildcard ↔ ids |
| `delete(id)` | Valida existencia y borra |

### 4.3 `TalentoTechService`

| Método | Comportamiento |
|---|---|
| `get_all_paginado`, `get_by_carrera_paginado`, `get_by_categoria_paginado` | Listados con orden estable |
| `get_by_id(id)` | `404` → `No se encontró el talentotech con ID: {id}` |
| `create(data)` | Resuelve carreras → unicidad `(institucion, nombre_curso)` → persiste |
| `update(id, data)` | Reemplazo total, con `exclude_id` en unicidad |
| `delete(id)` | Valida existencia y borra |

---

## 5. Routers y dependencias

- `routers/convenios.py`: declara `/carrera/{carrera_id}` antes que `/{convenio_id}`;
  `PUT`, `PATCH` y `DELETE` con `require_admin`.
- `routers/talentotech.py`: declara `/carrera/{carrera_id}` y
  `/categoria/{categoria}` antes que `/{talentotech_id}`; `POST`, `PUT` y
  `DELETE` con `require_admin`.

```python
get_convenio_service(db)    → ConvenioService(ConvenioRepository(db))
get_talentotech_service(db) → TalentoTechService(TalentoTechRepository(db))
```

---

## 6. Validaciones

| Regla | Implementación |
|---|---|
| Campos obligatorios | Pydantic (`schema.py`) |
| `link_info` / `link_inscripcion` | `HttpUrl` (solo `http`/`https`) en request |
| `strip()` de textos | `institucion`, `nombre_curso`, `carrera_destino`, `categoria`, `descripcion`, `duracion`, `modalidad_cursada` |
| `dificultad` | Opcional; nullable; **no** pasa por `strip` |
| Límites 150/20/50/30 | Solo a nivel de columna (PostgreSQL); Pydantic no valida `max_length` |
| `carrera_ids` mín. 1 | `_resolver_conjunto` cuando `todas_las_carreras = false` |
| Flag e ids excluyentes | `_resolver_conjunto` (422) |
| Carreras inexistentes | `_validar_carreras` (422) |
| Unicidad convenios | `(institucion, carrera_destino)` → 409 |
| Unicidad TalentoTech | `(institucion, nombre_curso)` → 409 |
| Escritura | `require_admin` → 403 estudiante, 401 sin/invalid token |
| Lectura | GET sin auth |
| Paginación | `PaginatedResponse` (`page`, `per_page` 1–100) |

---

## 7. Errores

| Código | Endpoints | Causa |
|---|---|---|
| `401` | POST/PUT/PATCH/DELETE | Sin token (`Not authenticated`) o token inválido |
| `403` | POST/PUT/PATCH/DELETE | No es admin (`Se requieren permisos de administrador`) |
| `404` | GET by id, PUT, PATCH, DELETE | Recurso inexistente |
| `409` | POST/PUT/PATCH | Duplicado de la clave única |
| `409` | DELETE / carreras | Violación de integridad no controlada (`Conflicto de integridad de datos`) |
| `422` | POST/PUT/PATCH | Carreras inexistentes, flag + ids, sin carreras, URL inválida, campos faltantes |

Formato:

```json
{ "detail": "mensaje" }
```

Los `422` de Pydantic agregan el detalle por campo:

```json
{ "detail": "Field required", "errors": [{ "campo": "link_info", "msg": "Field required" }] }
```

---

## 8. Seed

| Comando | Efecto | Idempotencia |
|---|---|---|
| `python seed.py` | Seed completo | — |
| `python seed.py --convenios` | Carga `CONVENIOS_SEED` sin borrar datos | `(institucion, carrera_destino)` |
| `python seed.py --talentotech` | Carga `TALENTOTECH_SEED` sin borrar datos | `(institucion, nombre_curso)` |

Ambos aceptan `carrera_ids` o `todas_las_carreras` y tienen el atajo `carrera`
(clave de `CARRERAS_SEED`) solo para convenios heredados.

---

## 9. Tests

- `tests/test_convenios.py`: contrato N:M, wildcard, PATCH, `q`, unicidad,
  orden case-insensitive, errores.
- `tests/test_talentotech.py`: card, flag ↔ ids, carreras múltiples, unicidad,
  filtros por carrera/categoría, orden, `PUT`/`DELETE`.
- `tests/test_authorization.py`: 401/403 en escritura de ambos recursos.

```powershell
$env:DATABASE_URL="sqlite:///./_pytest.db"
python -m pytest tests/test_convenios.py tests/test_talentotech.py -q
```
