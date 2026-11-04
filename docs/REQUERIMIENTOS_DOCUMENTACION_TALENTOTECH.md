# Requerimientos — Documentación de TalentoTech (backend)

> **Handoff para el agente de backend/documentación.**
> Fecha: 2026-11-03.
> Estado: API implementada y verificada; la documentación de `documentacion/` y
> `DOCUMENTACION_TECNICA_BACKEND.md` quedó desactualizada.
>
> **Fuentes de verdad**, en este orden:
> 1. Código actual: `app/features/recursos/{model,schema,repository,service,routers/talentotech}.py`
> 2. `docs/TALENTOTECH_FRONT.md` (contrato para el front)
> 3. `context/requirements.md` (RF-37…RF-41) y `context/decisions.md` (D20)
> 4. `tests/test_talentotech.py`
> 5. `docs/openapi.json` (generado)
>
> Si este documento contradice el código, **gana el código**. Si encontrás una
> discrepancia real, reportala; no modifiques código de aplicación dentro de
> esta tarea de documentación.

---

## 1. Objetivo

Actualizar y completar la documentación del backend para que refleje el
contrato vigente de **TalentoTech**:

- relación N:M entre cursos y carreras de origen;
- flag `todas_las_carreras`;
- campos nuevos (`institucion`, `modalidad_cursada`, `dificultad` opcional);
- respuesta de card con `carreras: CarreraResumen[]`;
- unicidad por `(institucion, nombre_curso)`;
- `PUT` de reemplazo total (no existe `PATCH`).

**No se pide cambiar la API ni el esquema.** El objetivo es que la
documentación describa lo que ya está implementado y que desaparezcan las
referencias obsoletas a `carrera_id` en TalentoTech.

---

## 2. Entregables

### 2.1 Crear

Crear la sección `documentacion/09-talentotech/` con cuatro archivos, siguiendo
el formato de las secciones existentes (`04-convenios`, `08-admin`):

| Archivo | Contenido |
|---|---|
| `documentacion/09-talentotech/api.md` | Contrato API: tipos, endpoints, ejemplos, errores. |
| `documentacion/09-talentotech/backend.md` | Modelo, tabla N:M, repositorio, servicio, router, validaciones. |
| `documentacion/09-talentotech/decisiones.md` | Decisiones de diseño y sus motivos (D20, N:M, wildcard, sin `PATCH`, etc.). |
| `documentacion/09-talentotech/frontend.md` | Consumo real desde `frontend-miifts`: features, servicios, filtros, formularios y tipos. |

### 2.2 Actualizar

| Archivo | Cambio requerido |
|---|---|
| `documentacion/04-convenios/api.md` | Quitar la parte de TalentoTech (tipos, endpoints, ejemplos, errores y servicios). Dejar Convenios y agregar un link a `../09-talentotech/api.md`. |
| `documentacion/04-convenios/backend.md` | Idem: quitar modelo/endpoints/servicios de TalentoTech y linkear a `09`. |
| `documentacion/04-convenios/frontend.md` | Idem: quitar la descripción de TalentoTech y linkear a `09`. |
| `documentacion/04-convenios/decisiones.md` | Quitar la decisión de categorías de TalentoTech o moverla a `09/decisiones.md`. |
| `documentacion/08-admin/api.md` | Agregar el bloque de endpoints admin de TalentoTech (`POST`, `PUT`, `DELETE`) con el body nuevo. |
| `documentacion/08-admin/backend.md` | Confirmar que las rutas admin de TalentoTech figuran y que la lectura pública está bien listada. |
| `documentacion/08-admin/frontend.md` | Agregar o linkear la pantalla `talentotech-admin` (tab “Talento Tech” del panel Admin). |
| `DOCUMENTACION_TECNICA_BACKEND.md` | Actualizar §5 “TalentoTech”, el mapa de tablas y la nota de auth/seguridad que todavía habla de `carrera_id`. |
| `DOCUMENTACION_TECNICA_FRONTEND.md` | Actualizar la estructura de `features/` y la sección “Convenios + TalentoTech” si se mantiene en el repo backend. |
| `docs/openapi.json` | Regenerar con `python scripts/export_openapi.py`; no editarlo a mano. Verificar que `TalentoTechCreate`/`TalentoTechResponse` tengan el shape nuevo. |
| `README.md` | Verificar la lista de endpoints (`/talentotech/`, `/talentotech/carrera/{id}`, `/talentotech/categoria/{cat}`). No duplicar el contrato completo acá. |
| `docs/TALENTOTECH_FRONT.md` | Corregir la tabla de errores 401/403 con los mensajes reales (ver §4.6). Si se toca, hacerlo con cuidado: es el contrato que consume el front. |

> **Consistencia al separar Convenios:** el `04-convenios` actual mezcla
> Convenios y TalentoTech. Al separarlo, verificá que Convenios no quede con
> `carrera_id` si el código ya usa `carrera_ids`/`todas_las_carreras` (D17). Si
> detectás esa deuda y excede el alcance de esta tarea, dejalo señalado en el
> reporte/PR en lugar de ignorarlo.

---

## 3. Contexto: qué cambió (breaking change)

| Antes (documentación vieja) | Ahora (código actual) |
|---|---|
| `carrera_id: number` en request y response | `carrera_ids: number[]` (N:M) **o** `todas_las_carreras: true` |
| Una sola carrera por curso | Un curso puede aplicar a varias carreras o a todas |
| Sin `institucion` | `institucion` obligatoria |
| Sin `modalidad_cursada` en la respuesta | `modalidad_cursada` obligatoria y presente |
| `dificultad` obligatoria / no persistida | `dificultad` opcional (`string \| null`) y persistida |
| `TalentoTechResponse` heredaba de `Create` | Response explícita con `id` y `carreras` |
| Sin restricción de duplicados | Único por `(institucion, nombre_curso)` → `409` |
| `PATCH` mencionado genéricamente | **No existe `PATCH`**: la edición es `PUT` completo |

Migración asociada: `alembic/versions/e8b3c1d5f7a9_talentotech_nm_carreras.py`.
La tabla `talentotech` ya **no tiene** `carrera_id`; la relación vive en
`talentotech_carreras`.

---

## 4. Requerimientos funcionales que la documentación debe reflejar

### 4.1 Modelo de datos

Tabla principal `talentotech`:

| Campo | Tipo SQL | Nulable | Límite | Notas |
|---|---|---:|---:|---|
| `id` | Integer PK | No | — | — |
| `institucion` | String | No | 150 | Se recorta (`strip`) en Pydantic. |
| `nombre_curso` | String | No | 150 | Se recorta. Orden alfabético por este campo. |
| `categoria` | String | No | 20 | Texto libre; no hay catálogo ni endpoint de categorías. Se recorta. |
| `descripcion` | Text | No | — | Se recorta. |
| `duracion` | String | No | 50 | Texto libre (ej. `"30hs"`). Se recorta. |
| `modalidad_cursada` | String | No | 50 | Texto libre (ej. `"Virtual Asincrónico"`). Se recorta. |
| `dificultad` | String | **Sí** | 30 | Opcional; `null` si no se envía. **No** pasa por el validador de `strip` del schema. |
| `link_inscripcion` | Text | No | — | En request es `HttpUrl` (solo `http`/`https`); en response es `string`. |
| `todas_las_carreras` | Boolean | No | — | Default `false`. `true` ⇒ aplica a todas las carreras. |

Tabla intermedia `talentotech_carreras`:

| Campo | Notas |
|---|---|
| `talentotech_id` | FK a `talentotech.id`, `ON DELETE CASCADE`, parte de la PK compuesta. |
| `carrera_id` | FK a `carreras.id`, parte de la PK compuesta. Sin cascada explícita. |

Restricciones:

- `UniqueConstraint("institucion", "nombre_curso", name="uq_talentotech_institucion_curso")`.
  Es **case-sensitive** y no pliega acentos: `"Curso X"` y `"curso x"` son
  distintos; `"Tecnologías"` y `"tecnologias"` también.
- La tabla principal no tiene `created_at` ni `updated_at`.
- Las carreras de un curso se devuelven ordenadas por `Carrera.nombre`.

### 4.2 Endpoints

| Método | Ruta | Auth | Body / query | Respuesta |
|---|---|---|---|---|
| `GET` | `/talentotech/` | Pública | `page`, `per_page` | `200 PaginatedResponse<TalentoTechResponse>` |
| `GET` | `/talentotech/carrera/{carrera_id}` | Pública | `page`, `per_page` | `200 PaginatedResponse<TalentoTechResponse>` |
| `GET` | `/talentotech/categoria/{categoria}` | Pública | `page`, `per_page` | `200 PaginatedResponse<TalentoTechResponse>` |
| `GET` | `/talentotech/{id}` | Pública | — | `200 TalentoTechResponse` / `404` |
| `POST` | `/talentotech/` | **Admin** | `TalentoTechCreate` | `201 TalentoTechResponse` |
| `PUT` | `/talentotech/{id}` | **Admin** | `TalentoTechCreate` (completo) | `200 TalentoTechResponse` / `404` |
| `DELETE` | `/talentotech/{id}` | **Admin** | — | `204` sin body / `404` |

**No existe `PATCH`.** No lo documentes como disponible.

### 4.3 Tipos del contrato

Request `TalentoTechCreate`:

```ts
interface TalentoTechCreate {
  institucion: string;              // obligatorio, max 150 (columna)
  nombre_curso: string;             // obligatorio, max 150 (columna)
  categoria: string;                // obligatorio, max 20 (columna), texto libre
  descripcion: string;              // obligatorio
  duracion: string;                 // obligatorio, max 50 (columna)
  modalidad_cursada: string;        // obligatorio, max 50 (columna)
  dificultad?: string | null;       // opcional, max 30 (columna)
  link_inscripcion: string;         // HttpUrl http/https
  carrera_ids?: number[] | null;    // requerido si todas_las_carreras = false
  todas_las_carreras?: boolean;     // default false
}
```

Response `TalentoTechResponse`:

```ts
interface CarreraResumen {
  id: number;
  nombre: string;
}

interface TalentoTechResponse {
  id: number;
  institucion: string;
  nombre_curso: string;
  categoria: string;
  descripcion: string;
  duracion: string;
  modalidad_cursada: string;
  dificultad: string | null;
  link_inscripcion: string;
  todas_las_carreras: boolean;
  carreras: CarreraResumen[];       // [] si todas_las_carreras = true
}
```

Envoltorio paginado:

```ts
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;                 // default 20, máximo 100
  total_pages: number;
}
```

### 4.4 Reglas de negocio e invariantes

1. **Flag ↔ ids excluyentes:**
   - `todas_las_carreras = true` ⇒ `carreras = []`, no se guardan filas en
     `talentotech_carreras` y **no** se debe enviar `carrera_ids` con contenido.
   - `todas_las_carreras = false` (o ausente) ⇒ `carrera_ids` con **al menos un
     id existente**.
   - `carrera_ids: []` se trata como ausente. Si el flag es `true`, una lista
     vacía no genera error; si el flag es `false`, sí (`422`).
2. **Carreras inexistentes:** cualquier id que no exista produce `422` con el
   detalle de los ids faltantes.
3. **Deduplicación:** `carrera_ids` se deduplica preservando el orden.
4. **Wildcard:** un curso con `todas_las_carreras = true` aparece en
   `GET /talentotech/carrera/{id}` para **cualquier carrera existente**,
   incluida una carrera creada después. No genera filas en la tabla intermedia.
5. **Filtro por carrera:** devuelve los cursos explícitos de esa carrera **más**
   los wildcard, sin duplicar filas. Si la carrera no existe, devuelve
   **lista vacía `200`** (no `404`), aunque existan cursos wildcard.
6. **Filtro por categoría:** igualdad exacta y case-sensitive; sin comodines.
   Categoría sin cursos ⇒ lista vacía `200`.
7. **Unicidad:** duplicar `(institucion, nombre_curso)` ⇒ `409`. No importa si
   cambian las carreras ni la categoría.
8. **Edición:** `PUT` reemplaza **todos** los campos y el conjunto de carreras.
   Pasar a wildcard borra las filas explícitas de la intermedia.
9. **Borrado:** `DELETE` elimina el curso y sus asociaciones. Si se intenta
   borrar una carrera que tiene cursos explícitos, PostgreSQL puede bloquearlo
   por FK y la API responde `409` genérico; SQLite local no fuerza FKs por
   defecto.
10. **Orden estable:** todos los listados ordenan por
    `lower(nombre_curso) ASC, id ASC` (alfabético case-insensitive).
11. **Sin búsqueda `q`:** no existe búsqueda textual en TalentoTech.
12. **Sin endpoint de categorías:** `categoria` es texto libre. No documentes
    un `GET /talentotech/categorias`.
13. **Sin timestamps:** no hay `created_at`/`updated_at` en el modelo ni en la
    respuesta.
14. **Rutas:** `/carrera/{carrera_id}` y `/categoria/{categoria}` se declaran
    antes que `/{talentotech_id}`; el `{id}` es numérico.

### 4.5 Validaciones y límites

- **Pydantic** valida:
  - campos obligatorios;
  - `link_inscripcion` como `HttpUrl` (solo `http`/`https`);
  - `carrera_ids` como lista de enteros;
  - `todas_las_carreras` booleano (default `false`);
  - `strip()` sobre `institucion`, `nombre_curso`, `categoria`, `descripcion`,
    `duracion` y `modalidad_cursada`.
- **Pydantic no valida `max_length`** para los textos: los límites de 150/20/50/30
  son de columna. En PostgreSQL se aplican; en SQLite local pueden no
  aplicarse. El frontend los valida en el formulario. La documentación debe
  decir “límite de columna” y no prometer un `422` de Pydantic por exceso.
- `dificultad` no se recorta en el backend. Si el front manda `""`, se guarda
  `""`; para representar “sin dificultad” debe mandar `null` o omitir el campo.
- Los textos se recortan **antes** de validar unicidad; dos payloads que solo
  difieren en espacios al borde terminan en el mismo `(institucion,
  nombre_curso)` y producen `409`.

### 4.6 Errores reales

| Código | Cuándo | Body |
|---|---|---|
| `401` | Falta el header `Authorization` | `{ "detail": "Not authenticated" }` |
| `401` | Token inválido o expirado | `{ "detail": "Token inválido o expirado" }` |
| `403` | Token válido de estudiante en `POST`/`PUT`/`DELETE` | `{ "detail": "Se requieren permisos de administrador" }` |
| `404` | `GET`/`PUT`/`DELETE` con id inexistente | `{ "detail": "No se encontró el talentotech con ID: 42" }` |
| `409` | Duplicado `(institucion, nombre_curso)` | `{ "detail": "Ya existe un curso TalentoTech con la misma institución y nombre" }` |
| `409` | Violación de integridad no controlada (p. ej. FK al borrar una carrera en Postgres) | `{ "detail": "Conflicto de integridad de datos" }` |
| `422` | Carrera(s) inexistente(s) | `{ "detail": "No existen las carreras: 4, 7" }` o `{ "detail": "No existe la carrera 4" }` |
| `422` | `todas_las_carreras: true` + `carrera_ids` no vacío | `{ "detail": "Si 'todas_las_carreras' es true no se debe enviar 'carrera_ids'" }` |
| `422` | Sin carreras y sin flag | `{ "detail": "Debe indicar al menos una carrera en 'carrera_ids' o marcar 'todas_las_carreras'" }` |
| `422` | Error de validación de Pydantic | `{ "detail": "<primer mensaje>", "errors": [{ "campo": "...", "msg": "..." }] }` |

> **Corrección requerida:** `docs/TALENTOTECH_FRONT.md` §5 dice `401 ->
> "No autenticado"` y `403 -> "No tenés permiso para esta operación"`. Esos
> mensajes **no** son los que devuelve el código actual. Actualizá la tabla con
> los valores reales de arriba.
>
> Los `422` de reglas de dominio (carreras, flag/ids) traen **solo `detail`**.
> Solo los `422` de Pydantic traen `errors[]`.

### 4.7 Auth

- Lectura (`GET`): pública, sin token.
- Escritura (`POST`/`PUT`/`DELETE`): `Authorization: Bearer <token>` de un
  usuario con rol `admin` (`require_admin`).
- Token de estudiante en escritura: `403`.
- Sin token / token inválido: `401`.

### 4.8 Ejemplos que deben figurar

Mínimo:

1. `GET /talentotech/?page=1&per_page=20` con un curso wildcard.
2. `GET /talentotech/carrera/2?per_page=100` mostrando que incluye wildcard.
3. `GET /talentotech/categoria/IT?per_page=100`.
4. `POST /talentotech/` con `carrera_ids: [1, 3]`.
5. `POST /talentotech/` con `todas_las_carreras: true`.
6. `PUT /talentotech/{id}` con body completo (mismo shape que POST).
7. `DELETE /talentotech/{id}` → `204`.
8. Ejemplo de `409` por duplicado y de `422` por flag + ids.

Usar `"institucion": "Agencia de Habilidades para el Futuro"`,
`"nombre_curso": "Tecnologías Emergentes"`, `"categoria": "IT"`,
`"duracion": "30hs"`, `"modalidad_cursada": "Virtual Asincrónico"` y
`"dificultad": null` para que coincida con `docs/DATA_TALENTOTECH.md`.

---

## 5. Contenido mínimo por documento

### 5.1 `documentacion/09-talentotech/api.md`

- Tipos `TalentoTechCreate`, `TalentoTechResponse`, `CarreraResumen`,
  `PaginatedResponse<T>`.
- Tabla de endpoints con auth, params, body y status.
- Ejemplos de §4.8.
- Tabla de errores de §4.6.
- Servicios del frontend (nombres reales, ver §5.4).
- Aclaraciones: sin `PATCH`, sin `q`, sin endpoint de categorías, sin
  timestamps, límites de columna.

### 5.2 `documentacion/09-talentotech/backend.md`

- Modelo `TalentoTech` y tabla `talentotech_carreras` con constraints,
  `ondelete` y orden de carreras.
- Migración `e8b3c1d5f7a9_talentotech_nm_carreras.py`.
- `TalentoTechRepository`: `query_all`, `query_by_carrera`, `query_by_categoria`,
  `get_by_unique_key`, `create/update/delete`, orden estable.
- `TalentoTechService`: `_resolver_conjunto`, `_validar_carreras`,
  `_validar_unicidad`, `get_*`, `create`, `update`, `delete`.
- Router `routers/talentotech.py`: orden de rutas y dependencias.
- Dependencia `get_talentotech_service`.
- Reglas de §4.4 y validaciones de §4.5.
- Errores de §4.6.
- Nota de seed: `python seed.py --talentotech` es idempotente por
  `(institucion, nombre_curso)`.

### 5.3 `documentacion/09-talentotech/decisiones.md`

Documentar, como mínimo:

- **D20**: replicar en TalentoTech el modelo N:M + flag de Convenios (D17).
- Por qué se eliminó `carrera_id` del request/response (breaking change).
- Por qué `todas_las_carreras` y `carrera_ids` son excluyentes.
- Por qué `dificultad` es opcional y nullable.
- Por qué no hay `PATCH` (PUT de reemplazo total).
- Por qué `categoria` es texto libre y el filtro es exacto/case-sensitive.
- Por qué una carrera inexistente devuelve lista vacía en vez de `404`.
- Por qué no hay timestamps.
- Consecuencia de FK al borrar carreras con cursos explícitos.

### 5.4 `documentacion/09-talentotech/frontend.md`

Debe reflejar la implementación real en `frontend-miifts`:

| Área | Archivos / comportamiento |
|---|---|
| Sección estudiante | `src/features/talentotech/` (`TalentoTechSection.tsx`, `TalentoTechCard.tsx`, `TalentoTechDetalleModal.tsx`, `service.ts`, `hooks.ts`). |
| Sección admin | `src/features/talentotech-admin/` (`TalentoTechAdminScreen.tsx`, `talentoTechSpec.ts`, `service.ts`, `hooks.ts`). |
| Integración | La sección del estudiante se renderiza como pestaña **“Talento Tech”** dentro de `features/convenios/ConveniosScreen.tsx`. El admin la agrega como tercera tab en `features/admin/AdminScreen.tsx`. |
| Tipos | `TalentoTech`/`TalentoTechCreate` salen de `src/api/schema.d.ts` (regenerado con `npm run gen:api`). |
| Listado | Paginación real; filtro por categoría con `/talentotech/categoria/{cat}`; filtro “Solo mi carrera” con `/talentotech/carrera/{id}` usando `usuario.carrera_id`; sin búsqueda textual. |
| Categorías | Como no hay endpoint de categorías, el `<select>` se puebla con un catálogo acotado (`per_page=100`) y agrega la categoría activa. Si hubiera más de 100 cursos, las opciones podrían quedar incompletas. |
| Detalle | Modal con `descripcion`, `duracion`, `modalidad_cursada`, `dificultad` (si no es `null`), disponibilidad y CTA a `link_inscripcion` en pestaña nueva. |
| ABM admin | Alta con `POST`, edición con `PUT` completo, baja con `DELETE`; selector múltiple de carreras o switch “Todas las carreras”; validación de URL; máximo de caracteres; `409`/`422` mapeados a toast/campos. |
| Tipos de formulario | `EntityForm` soporta `textarea` y `maxLength`. |
| Tests | `src/features/talentotech/TalentoTechSection.test.tsx` y `src/features/convenios/ConveniosScreen.test.tsx`. |

Aclarar que el backend **no** debe documentar como existentes endpoints que el
front resolvió por su cuenta (categorías, búsqueda, `PATCH`).

---

## 6. Requisitos de calidad de la documentación

- Markdown válido, con tablas y bloques de código cerrados.
- No duplicar el contrato completo en `04-convenios`, `08-admin` y `09`:
  `09` es la fuente y el resto linkea.
- No copiar logs ni salidas de tests.
- Usar los nombres reales de campos, rutas, status codes y mensajes.
- Distinguir claramente:
  - request vs response;
  - `TalentoTechCreate` vs `TalentoTechResponse`;
  - validación Pydantic vs constraint de base de datos;
  - error de dominio (`detail`) vs error de validación (`detail` + `errors[]`).
- Los ejemplos deben ser ejecutables (URLs, headers y JSON coherentes).
- No inventar endpoints, campos, enums ni códigos de error.

---

## 7. Criterios de aceptación

- [ ] Existe `documentacion/09-talentotech/` con los cuatro archivos.
- [ ] `09/api.md` contiene tipos, endpoints, ejemplos y errores de §4.
- [ ] `09/backend.md` contiene modelo, tabla N:M, repositorio, servicio, router
      y validaciones.
- [ ] `09/decisiones.md` documenta D20 y las decisiones de §5.3.
- [ ] `09/frontend.md` refleja las features reales de §5.4.
- [ ] `04-convenios/*` ya no documenta el contrato viejo de TalentoTech y
      linkea a `09`.
- [ ] `08-admin/*` incluye los endpoints admin de TalentoTech con el body nuevo.
- [ ] `DOCUMENTACION_TECNICA_BACKEND.md` ya no dice que TalentoTech tiene
      `carrera_id`.
- [ ] `docs/TALENTOTECH_FRONT.md` tiene los mensajes reales de 401/403.
- [ ] `docs/openapi.json` fue regenerado y coincide con el código.
- [ ] `grep -R "carrera_id" documentacion/09-talentotech DOCUMENTACION_TECNICA_BACKEND.md`
      no devuelve usos del contrato viejo (solo puede aparecer al explicar la
      migración o la tabla intermedia).
- [ ] No se modificó código de aplicación.
- [ ] El reporte final indica qué se actualizó, qué se verificó y qué deuda
      quedó fuera de alcance.

---

## 8. Verificación sugerida

```powershell
cd C:\Users\gonza\source\repos\ProyectoIntegrador\backend-ifts

# Tests del contrato
.\.venv\Scripts\python.exe -m pytest tests/test_talentotech.py -q

# Regenerar OpenAPI versionado
.\.venv\Scripts\python.exe scripts/export_openapi.py

# Buscar referencias obsoletas
Select-String -Path documentacion\**\*.md,DOCUMENTACION_TECNICA_BACKEND.md -Pattern "carrera_id" -CaseSensitive:$false
```

Verificación manual mínima contra la API local:

```powershell
$login = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/auth/login" `
  -ContentType "application/json" `
  -Body '{"email":"admin@miifts.ar","password":"admin1234"}'
$headers = @{ Authorization = "Bearer $($login.access_token)" }

# Listado
Invoke-RestMethod "http://127.0.0.1:8000/talentotech/?per_page=100"

# Por carrera (incluye wildcard)
Invoke-RestMethod "http://127.0.0.1:8000/talentotech/carrera/1?per_page=100"

# Por categoría (exacta)
Invoke-RestMethod "http://127.0.0.1:8000/talentotech/categoria/IT?per_page=100"
```

> En PowerShell, para bodies con acentos usar
> `[System.Text.Encoding]::UTF8.GetBytes($body)` y
> `Content-Type: application/json; charset=utf-8`; de lo contrario el backend
> puede responder `{"detail":"There was an error parsing the body"}`.

---

## 9. Fuera de alcance / brechas detectadas

Estas brechas **no** deben documentarse como funcionalidades existentes. Si el
equipo quiere implementarlas, requieren su propio requerimiento y decisión:

| Brecha | Consecuencia actual |
|---|---|
| No hay `GET /talentotech/categorias` | El front arma las opciones con un catálogo de hasta 100 cursos; puede quedar incompleto. |
| No hay búsqueda `q` | El listado no tiene búsqueda textual. |
| No hay `PATCH` | El admin envía el body completo en cada edición. |
| `TalentoTechCreate` no declara `max_length` | El exceso de longitud depende de la columna/DB; el front lo previene. |
| `dificultad` no se recorta | `""` y `null` son valores distintos. |
| Mensajes 401/403 del doc del front desactualizados | Corregirlos en `docs/TALENTOTECH_FRONT.md`. |

No cambiar la API para “hacer más fácil” la documentación. Si al documentar
aparece una discrepancia entre código y contrato, reportarla al Planner/Arquitecto
antes de tocar código.

---

## 10. Referencias

- `context/requirements.md` — RF-37…RF-41, AC-15…AC-20.
- `context/decisions.md` — D17, D20.
- `context/status.md` — estado de la implementación de TalentoTech.
- `docs/TALENTOTECH_FRONT.md` — contrato para el front.
- `docs/DATA_TALENTOTECH.md` — dato de ejemplo y seed.
- `docs/openapi.json` — spec generada.
- `app/features/recursos/model.py`, `schema.py`, `repository.py`, `service.py`,
  `routers/talentotech.py`.
- `tests/test_talentotech.py`.
- `alembic/versions/e8b3c1d5f7a9_talentotech_nm_carreras.py`.
- Frontend: `frontend-miifts/src/features/talentotech/`,
  `frontend-miifts/src/features/talentotech-admin/`,
  `frontend-miifts/src/features/convenios/ConveniosScreen.tsx`,
  `frontend-miifts/src/features/admin/AdminScreen.tsx`.
