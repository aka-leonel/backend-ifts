# Data de TalentoTech — ingesta local y Postgres

> Contrato de API para el front: `docs/TALENTOTECH_FRONT.md`.
> Curso provisto por el usuario el 2026-11-03, normalizado al contrato de
> TalentoTech (N:M con carreras de origen + `todas_las_carreras`).
> Idempotente por `(institucion, nombre_curso)`.

## 1. Dato (JSON para la API)

```json
[
  {
    "todas_las_carreras": true,
    "institucion": "Agencia de Habilidades para el Futuro",
    "nombre_curso": "Tecnologías Emergentes",
    "categoria": "IT",
    "descripcion": "En este curso te sumergirás en aquellas revoluciones que están transformando al mundo, pero sobre todo, a los humanos. La idea detrás de este programa es que no podemos entender la inteligencia artificial, la robótica, el blockchain, el internet de las cosas o la realidad virtual como elementos separados, sino más bien como revoluciones convergentes, que se relacionan y potencian una a otra.",
    "duracion": "30hs",
    "modalidad_cursada": "Virtual Asincrónico",
    "link_inscripcion": "https://talentotech.bue.edu.ar/home/inscripcion/adultos"
  }
]
```

> **`modalidad_cursada`**: valor final confirmado por el usuario:
> `"Virtual Asincrónico"`.

## 2. Cómo ejecutar

### 2.1 SQLite local (`miifts.db`)

```powershell
$env:DATABASE_URL="sqlite:///./miifts.db"
python seed.py --talentotech
```

### 2.2 Postgres (Docker)

```powershell
docker compose up -d --build
docker compose exec -T api python seed.py --talentotech
```

### 2.3 Vía API

```powershell
$login = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/auth/login" `
  -ContentType "application/json" `
  -Body '{"email":"admin@miifts.ar","password":"admin1234"}'
$headers = @{ Authorization = "Bearer $($login.access_token)" }

$body = '{"todas_las_carreras":true,"institucion":"Agencia de Habilidades para el Futuro","nombre_curso":"Tecnologías Emergentes","categoria":"IT","descripcion":"...","duracion":"30hs","modalidad_cursada":"Virtual Asincrónico","link_inscripcion":"https://talentotech.bue.edu.ar/home/inscripcion/adultos"}'
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/talentotech/" `
  -Headers $headers -ContentType "application/json" -Body $body
```

## 3. Verificación

```sql
SELECT count(*) FROM talentotech;                -- 1
SELECT count(*) FROM talentotech_carreras;       -- 0 (wildcard)

SELECT id, institucion, nombre_curso, categoria, duracion,
       modalidad_cursada, dificultad, todas_las_carreras, link_inscripcion
FROM talentotech;

SELECT t.id, t.nombre_curso, string_agg(ca.nombre, ' | ') AS carreras
FROM talentotech t
LEFT JOIN talentotech_carreras tc ON tc.talentotech_id = t.id
LEFT JOIN carreras ca ON ca.id = tc.carrera_id
GROUP BY t.id;
```

```bash
curl "http://localhost:8000/talentotech/?per_page=100"
curl "http://localhost:8000/talentotech/carrera/1?per_page=100"   # debe incluirlo
```

## 4. Notas

- Como `todas_las_carreras = true`, el curso aparece en
  `GET /talentotech/carrera/{id}` para **cualquier** carrera existente.
- Si la carrera no existe, el endpoint devuelve vacío (mismo criterio que
  convenios).
- `dificultad` es opcional y quedó en `null`.
