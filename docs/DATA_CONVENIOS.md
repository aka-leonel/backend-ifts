# Data de convenios — ingesta local y Postgres

> Datos provistos por el usuario el 2026-10-28, normalizados al contrato vigente
> (N:M con carreras de origen + `todas_las_carreras`).
> Idempotente: se puede ejecutar las veces que haga falta sin duplicar.
>
> La clave de idempotencia es `(institucion, carrera_destino)`.

## 1. Mapeo de carreras

Los `carrera_ids` refieren a la tabla `carreras`. En un seed limpio:

| ID | Nombre |
|----|--------|
| 1 | Tecnicatura Superior en Desarrollo de Software |
| 2 | Tecnicatura Superior en Análisis de Sistemas |
| 3 | Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial |

> **Antes de ejecutar en otra base**, verificá que los IDs coincidan:
> `GET /materias/carreras` o `select id, nombre from carreras order by id;`.
> Si no coinciden, ajustá los `carrera_ids` de este archivo.

## 2. Datos (JSON para la API)

Array listo para `POST /convenios/` (requiere token admin). Cada ítem usa
`carrera_ids` **o** `todas_las_carreras`, nunca ambos.

```json
[
  {
    "carrera_ids": [1, 2],
    "institucion": "Universidad Nacional de la Matanza",
    "carrera_destino": "Licenciatura en Gestión de Tecnología",
    "descripcion": "Este Ciclo de Complementación Curricular tiene como propósito central fusionar las competencias técnicas de la informática con las herramientas de management y liderazgo empresarial, preparando a los graduados para conducir la transformación digital y administrar la infraestructura tecnológica de cualquier organización. A diferencia de una ingeniería tradicional centrada en el desarrollo puro de código o hardware, este ciclo se enfoca en cómo utilizar la tecnología para resolver problemas de negocios y optimizar procesos productivos",
    "link_info": "https://formacioncontinua.unlam.edu.ar/licenciatura-en-gestion-de-tecnologia/"
  },
  {
    "todas_las_carreras": true,
    "institucion": "Universidad de Palermo",
    "carrera_destino": "Licenciatura en Tecnología de la Información",
    "descripcion": "El Ciclo de Complementación de la Licenciatura en Tecnología de la Información forma profesionales enfocados en la conducción, desarrollo e implementación de tecnologías de software, hardware, comunicaciones, y los servicios relacionados, en todo tipo de negocios y organizaciones.",
    "link_info": "https://www.palermo.edu/ingenieria/complementacion-lic-en-tecnologia-de-la-informacion"
  },
  {
    "todas_las_carreras": true,
    "institucion": "Universidad de Palermo",
    "carrera_destino": "Licenciatura en Redes y Comunicación de Datos",
    "descripcion": "La Licenciatura en Redes y Comunicación de Datos en la UP es la carrera en Argentina más reconocida en las redes de comunicaciones de datos, sus protocolos, arquitectura, administración, integración y análisis. Sus egresados son los profesionales más destacados en la Industria de Servicios de Telecomunicaciones.",
    "link_info": "https://www.palermo.edu/ingenieria/complementacion_redes_comunicacion/index.html"
  },
  {
    "carrera_ids": [2],
    "institucion": "Universidad de Palermo",
    "carrera_destino": "Licenciatura en Administración de Sistemas y Empresas",
    "descripcion": "Forma profesionales para liderar y desarrollar sistemas en empresas e introducir innovaciones que generen nuevos negocios.",
    "link_info": "https://www.palermo.edu/negocios/ciclo-administracion-sistemas-y-empresas"
  },
  {
    "todas_las_carreras": true,
    "institucion": "Universidad de la Ciudad de Buenos Aires",
    "carrera_destino": "Licenciatura en Tecnologías Digitales",
    "descripcion": "La Licenciatura en Tecnologías Digitales forma profesionales expertos en tecnologías digitales de innovación, capaces de ser referentes en los procesos de transformación digital que generen valor agregado en organizaciones privadas, públicas y ONG, destacándose por la innovación, adaptabilidad al cambio y la gestión del mundo de los negocios, su contribución al desarrollo local y regional con altos estándares éticos y de compromiso social.",
    "link_info": "https://www.udelaciudad.edu.ar/licenciatura-en-tecnologias-digitales/"
  },
  {
    "carrera_ids": [3],
    "institucion": "Universidad de la Ciudad de Buenos Aires",
    "carrera_destino": "Licenciatura en Ciencia de Datos",
    "descripcion": "Por medio de la Licenciatura en Ciencia de Datos (CCC) forma profesionales capacitados para analizar, interpretar y transformar datos en información estratégica para la toma de decisiones en distintos tipos de organizaciones. El graduado desarrolla competencias en análisis de datos, herramientas tecnológicas y resolución de problemas complejos, destacándose por la innovación, la adaptabilidad al cambio y el uso ético de la información, contribuyendo al desarrollo local y regional con compromiso social.",
    "link_info": "https://www.udelaciudad.edu.ar/licenciatura-en-ciencia-de-datos/"
  },
  {
    "todas_las_carreras": true,
    "institucion": "Universidad de la Ciudad de Buenos Aires",
    "carrera_destino": "Licenciatura en Desarrollo y Producción de Videojuegos",
    "descripcion": "Estudiar la Licenciatura en Desarrollo y Producción de Videojuegos (Ciclo de Complementación Curricular) en la UdelaCiudad permite formarse en una industria en crecimiento, adquiriendo una sólida formación en diseño, programación y producción de videojuegos, junto con competencias en gestión de proyectos, liderazgo y desarrollo de emprendimientos digitales, en un sector estratégico de la economía del conocimiento.",
    "link_info": "https://www.udelaciudad.edu.ar/licenciatura-en-desarrollo-y-produccion-de-videojuegos"
  },
  {
    "todas_las_carreras": true,
    "institucion": "Universidad Nacional de Lanús",
    "carrera_destino": "Licenciatura en Tecnologías Digitales para la Educación",
    "descripcion": "Durante el Ciclo aprenderás sobre los nuevos escenarios educativos a partir de la utilización de tecnologías digitales; conocerás aplicaciones libres destinadas a la enseñanza y el aprendizaje; y trabajarás en distintas propuestas pedagógicas que involucren activamente a sus estudiantes",
    "link_info": "https://www.unla.edu.ar/carreras/grado/ciclos-de-licenciatura/tecnologias-digitales-para-la-educacion"
  },
  {
    "carrera_ids": [2, 3],
    "institucion": "Universidad Nacional de Lomas de Zamora",
    "carrera_destino": "Licenciatura en Gestión de la Información",
    "descripcion": "La Licenciatura en Gestión de la Información tiene por objetivo formar profesionales con sólida formación teórica, metodológica y técnica en la gestión de la información, integrando los aspectos teóricos y prácticos de las disciplinas de la gestión de la información a las nuevas nuevas tecnologías y adecuando la formación profesional a las exigencias del mercado laboral.",
    "link_info": "https://ingenieria.unlz.edu.ar/oferta-academica/grado#licenciaturas"
  },
  {
    "carrera_ids": [1, 3],
    "institucion": "Universidad Nacional de Lomas de Zamora",
    "carrera_destino": "Gestión de Sistemas de Automatización y Robótica",
    "descripcion": "Los/as graduados/as de la Licenciatura en Gestión de Sistemas de Automación y Robótica serán capaces de integrar equipos de planificación, desarrollo y gestión de sistemas integrados de procesos productivos y de colaborar en el análisis y simulación de sistemas automáticos de producción y fabricación. A su vez, estarán habilitados para participar tanto en la conducción de equipos de trabajo destinados a tareas de producción como también en investigaciones de técnicas y procedimientos relacionados con su campo de estudio.",
    "link_info": "https://ingenieria.unlz.edu.ar/oferta-academica/grado#licenciaturas"
  }
]
```

## 3. Datos para el seed (`CONVENIOS_SEED`)

Ya están cargados en `seed.py` (lista `CONVENIOS_SEED`). La misma información en
formato Python por si hay que recrearla:

```python
CONVENIOS_SEED = [
    {"carrera_ids": [1, 2], "institucion": "Universidad Nacional de la Matanza",
     "carrera_destino": "Licenciatura en Gestión de Tecnología",
     "descripcion": "...", "link_info": "https://formacioncontinua.unlam.edu.ar/licenciatura-en-gestion-de-tecnologia/"},
    {"todas_las_carreras": True, "institucion": "Universidad de Palermo",
     "carrera_destino": "Licenciatura en Tecnología de la Información",
     "descripcion": "...", "link_info": "https://www.palermo.edu/ingenieria/complementacion-lic-en-tecnologia-de-la-informacion"},
    # ... ver `seed.py` para el texto completo de las 10 descripciones
]
```

## 4. Cómo ejecutar

### 4.1 Ingesta local (SQLite, `miifts.db`)

Desde la raíz del repo:

```powershell
$env:DATABASE_URL="sqlite:///./miifts.db"

# Solo si la base local está vacía: crea IFTS, carreras, materias y usuarios demo.
python seed.py

# Carga (o completa) los convenios sin borrar nada. Idempotente.
python seed.py --convenios
```

Estado actual: **`miifts.db` ya sembrado con 10 convenios** (5 wildcard + 5 con
carreras explícitas; 8 filas en `convenios_carreras`).

### 4.2 Ingesta en Postgres (Docker)

La base Postgres vive en el contenedor `db` y no expone puerto al host. Por eso
los comandos se ejecutan dentro del contenedor `api`:

```powershell
docker compose up -d --build          # aplica migraciones (alembic upgrade head)
docker compose exec -T api python seed.py --convenios
docker compose exec -T api python seed.py --admin   # crea el admin si no existe
```

Si además querés recrear todo el catálogo (¡borra datos!):

```powershell
docker compose exec -T api python seed.py
```

Estado actual: **Postgres sembrado con 10 convenios** y con usuario admin
(`admin@miifts.ar` / `admin1234`). El catálogo de carreras se normalizó a los
IDs 1/2/3 del seed (ver §6).

### 4.3 Ingesta vía API (server levantado)

Requiere el server arriba en `http://localhost:8000` y credenciales admin
(`admin@miifts.ar` / `admin1234` en un seed limpio).

```powershell
# 1. Login
$login = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/auth/login" `
  -ContentType "application/json" `
  -Body '{"email":"admin@miifts.ar","password":"admin1234"}'
$headers = @{ Authorization = "Bearer $($login.access_token)" }

# 2. POST de cada convenio (el JSON del §2, ítem por ítem)
$body = '{"carrera_ids":[1,2],"institucion":"Universidad Nacional de la Matanza","carrera_destino":"Licenciatura en Gestión de Tecnología","descripcion":"...","link_info":"https://formacioncontinua.unlam.edu.ar/licenciatura-en-gestion-de-tecnologia/"}'
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/convenios/" `
  -Headers $headers -ContentType "application/json" -Body $body
```

Un `POST` repetido devuelve `409` por la clave única, así que también es seguro
reejecutar.

## 5. Verificación

```sql
-- Postgres
SELECT count(*) FROM convenios;              -- 10
SELECT count(*) FROM convenios_carreras;     -- 8

SELECT cv.id, cv.institucion, cv.carrera_destino, cv.todas_las_carreras,
       string_agg(ca.nombre, ' | ') AS carreras
FROM convenios cv
LEFT JOIN convenios_carreras cc ON cc.convenio_id = cv.id
LEFT JOIN carreras ca ON ca.id = cc.carrera_id
GROUP BY cv.id
ORDER BY cv.id;
```

```bash
# API
curl "http://localhost:8000/convenios/?per_page=100"
curl "http://localhost:8000/convenios/carrera/1?per_page=100"
curl "http://localhost:8000/convenios/carrera/3?per_page=100"
```

Resultado esperado por carrera de origen:

| Carrera | Total | Convenios explícitos + wildcard |
|---|---|---|
| 1 — Desarrollo de Software | 7 | UNLaM Gestión de Tecnología, UNLZ Automatización y Robótica + 5 wildcard |
| 2 — Análisis de Sistemas | 8 | UNLaM Gestión de Tecnología, UP Administración de Sistemas y Empresas, UNLZ Gestión de la Información + 5 wildcard |
| 3 — Ciencia de Datos | 8 | UdeCiudad Ciencia de Datos, UNLZ Gestión de la Información, UNLZ Automatización y Robótica + 5 wildcard |

## 6. Notas y observaciones de los datos

1. **Catálogo de carreras de Postgres normalizado**: estaba con dos carreras
   homónimas ("Desarrollo de Software", ids 1 y 2) y sin id 3. Se alineó sin
   borrar datos a:
   - id 1 → Tecnicatura Superior en Desarrollo de Software
   - id 2 → Tecnicatura Superior en Análisis de Sistemas
   - id 3 → Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial (nueva)

   No se borraron usuarios ni otras tablas.

2. **Correcciones aplicadas**:
   - Videojuegos: `link_info` → `https://www.udelaciudad.edu.ar/licenciatura-en-desarrollo-y-produccion-de-videojuegos`.
   - "Universidad de la **Ciudad** de Buenos Aires" (antes `Cuidad`).
   - "Universidad Nacional de **Lanús**" (antes `Lanus`).
   - UNLZ *Licenciatura en Gestión de la Información*: carreras de origen `[2, 3]`
     (antes `[1, 3]`).
   - Nuevo convenio UNLZ *Gestión de Sistemas de Automatización y Robótica* para
     las carreras `[1, 3]`.

3. **Link del nuevo convenio UNLZ**: el ítem vino sin `link_info` y el campo es
   obligatorio. Se usó la misma página de oferta de UNLZ que el otro convenio
   (`https://ingenieria.unlz.edu.ar/oferta-academica/grado#licenciaturas`).
   Si corresponde una URL específica, se puede corregir con `PATCH`.

4. Los `carrera_id` singulares del input original se normalizaron a `carrera_ids`
   (array), que es el contrato vigente.

5. **Admin en Postgres**: se creó `admin@miifts.ar` / `admin1234` (rol `ADMIN`)
   con `python seed.py --admin`. Es idempotente por email.

6. **Orden del listado**: ahora es case-insensitive
   (`lower(institucion) ASC, id ASC`), así que el orden natural es
   "Universidad de la Ciudad…" → "Universidad de Palermo" → "Universidad Nacional…".
