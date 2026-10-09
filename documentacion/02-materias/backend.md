# Materias - Backend

## Endpoints

### Carreras (público lectura, admin escritura)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/materias/carreras` | Lista paginada |
| GET | `/materias/carreras/{id}` | Detalle |
| POST | `/materias/carreras` | Crea (nombre, duración, ifts_id) |
| PUT | `/materias/carreras/{id}` | Actualiza |
| DELETE | `/materias/carreras/{id}` | Elimina (409 si tiene materias) |

### Materias (público lectura, admin escritura)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/materias/carrera/{carrera_id}` | Materias por carrera (paginado) |
| GET | `/materias/buscar?q=...&anio=&cuatrimestre=` | **Búsqueda texto libre** (RF-21) |
| GET | `/materias/{id}` | Detalle |
| POST | `/materias/` | Crea (carrera_id, nombre, código, año, cuatrimestre) |
| PUT | `/materias/{id}` | Actualiza |
| DELETE | `/materias/{id}` | Elimina (409 si tiene cursadas) |

### Correlativas (público lectura, admin escritura)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/materias/correlativas/{materia_id}` | Lista paginada (incluye `requiere` embebido) |
| POST | `/materias/correlativas` | Crea `materia_id` → `requiere_id` (valida **ciclos** con DFS) |
| DELETE | `/materias/correlativas/{id}` | Elimina |

### Cursadas - `MateriaUsuario` (auth: propio o admin)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/materias/usuario/{usuario_id}` | Cursadas paginadas (con `materia_nombre`, `nota_final`, `estado`) |
| GET | `/materias/promedio/{usuario_id}` | Promedio notas finales (excluye `cursando` y `pendiente`) |
| POST | `/materias/usuario` | Agrega cursada (`materia_id`, `cursando`, notas opcionales) |
| PATCH | `/materias/cursada/{id}` | Actualiza notas / `cursando` / `examen_final` |
| DELETE | `/materias/cursada/{id}` | Elimina |

## Modelos

```python
# IFTS: id, nombre, ubicacion
# Carrera: id, nombre, duracion_cuatrimestres, ifts_id(FK)
# Materia: id, carrera_id(FK), nombre, codigo(único por carrera), anio, cuatrimestre
# Correlativa: id, materia_id(FK), requiere_id(FK) → unique(materia_id, requiere_id), self-referencial
# MateriaUsuario: id, usuario_id(FK), materia_id(FK), cursando, nota_parcial_1, nota_parcial_2, examen_final
#   unique(usuario_id, materia_id)
#   nota_final, estado: CALCULADOS en service (no columnas)
```

## Lógica de Negocio (service.py)

**Detección ciclos correlativas:** DFS desde `requiere_id` buscando `materia_id`. Si hay camino → 409 "generaría un ciclo".

**Cursada única:** `UniqueConstraint(usuario_id, materia_id)` + validación: materia debe ser de carrera del usuario.

**Estado derivado:**
```
cursando=true              → "cursando"
parcial1≥7 Y parcial2≥7    → "promocionada" (nota_final = round((p1+p2)/2, 2))
examen_final ≥ 4           → "aprobada"     (nota_final = examen_final)
examen_final < 4           → "desaprobada"  (nota_final = examen_final)
sin examen, no cursando    → "pendiente"    (nota_final = null)
```

**Promedio usuario:** Promedia `nota_final` de cursadas cerradas (excluye `cursando` y `pendiente`).

**Borrado seguro:** 409 si carrera tiene materias, o materia tiene cursadas.

## Schemas Response (clave)

```python
MateriaUsuarioResponse: id, usuario_id, materia_id, materia_nombre, cursando,
  nota_parcial_1, nota_parcial_2, examen_final,
  nota_final (calculado), estado (derivado)

PromedioResponse: promedio (float|null), materias_computadas (int)
```