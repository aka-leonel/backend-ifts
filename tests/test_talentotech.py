"""Cobertura del contrato de TalentoTech (card + N:M con carreras)."""


def _payload(carrera_ids=None, **overrides) -> dict:
    data = {
        "institucion": "Agencia de Habilidades para el Futuro",
        "nombre_curso": "Tecnologías Emergentes",
        "categoria": "IT",
        "descripcion": "Curso de tecnologías emergentes",
        "duracion": "30hs",
        "modalidad_cursada": "Virtual",
        "link_inscripcion": "https://ejemplo.com/inscripcion",
    }
    if carrera_ids is not None:
        data["carrera_ids"] = carrera_ids
    data.update(overrides)
    return data


def _crear(client, admin_headers, carrera_ids=None, **overrides) -> dict:
    r = client.post(
        "/talentotech/", json=_payload(carrera_ids, **overrides), headers=admin_headers
    )
    assert r.status_code == 201, r.text
    return r.json()


def _crear_carrera(db_session, nombre: str, ifts_id: int):
    from app.features.materias.model import Carrera

    carrera = Carrera(nombre=nombre, duracion_cuatrimestres=4, ifts_id=ifts_id)
    db_session.add(carrera)
    db_session.commit()
    db_session.refresh(carrera)
    return carrera


def _ids_carreras(curso: dict) -> list[int]:
    return [carrera["id"] for carrera in curso["carreras"]]


# ───────────────────────── Card completa (response) ─────────────────────────


def test_crear_devuelve_todos_los_campos_de_la_card(
    client, admin_headers, carrera_test
):
    curso = _crear(client, admin_headers, [carrera_test.id])

    assert curso["id"] > 0
    assert curso["institucion"] == "Agencia de Habilidades para el Futuro"
    assert curso["nombre_curso"] == "Tecnologías Emergentes"
    assert curso["categoria"] == "IT"
    assert curso["descripcion"] == "Curso de tecnologías emergentes"
    assert curso["duracion"] == "30hs"
    assert curso["modalidad_cursada"] == "Virtual"
    assert curso["dificultad"] is None
    assert curso["link_inscripcion"] == "https://ejemplo.com/inscripcion"
    assert curso["todas_las_carreras"] is False
    assert _ids_carreras(curso) == [carrera_test.id]


def test_crear_wildcard_devuelve_carreras_vacias(client, admin_headers):
    curso = _crear(client, admin_headers, todas_las_carreras=True)

    assert curso["todas_las_carreras"] is True
    assert curso["carreras"] == []


def test_crear_con_dificultad_opcional(client, admin_headers, carrera_test):
    curso = _crear(client, admin_headers, [carrera_test.id], dificultad="Media")

    assert curso["dificultad"] == "Media"


def test_crear_con_varias_carreras(client, admin_headers, carrera_test, db_session):
    """Mismo criterio que convenios: `carrera_ids` acepta una o varias."""
    otra = _crear_carrera(db_session, "Otra Carrera", carrera_test.ifts_id)

    curso = _crear(client, admin_headers, [carrera_test.id, otra.id])

    assert set(_ids_carreras(curso)) == {carrera_test.id, otra.id}
    assert curso["todas_las_carreras"] is False
    for carrera in (carrera_test, otra):
        r = client.get(f"/talentotech/carrera/{carrera.id}", params={"per_page": 50})
        assert [c["id"] for c in r.json()["items"]] == [curso["id"]]


# ───────────────────────── Invariantes flag ↔ carreras ─────────────────────────


def test_crear_sin_carreras_ni_flag_es_422(client, admin_headers):
    r = client.post("/talentotech/", json=_payload(), headers=admin_headers)

    assert r.status_code == 422, r.text


def test_crear_flag_y_carreras_es_422(client, admin_headers, carrera_test):
    r = client.post(
        "/talentotech/",
        json=_payload([carrera_test.id], todas_las_carreras=True),
        headers=admin_headers,
    )

    assert r.status_code == 422, r.text


def test_crear_carrera_inexistente_es_422(client, admin_headers):
    r = client.post("/talentotech/", json=_payload([999999]), headers=admin_headers)

    assert r.status_code == 422, r.text
    assert "999999" in r.text


def test_duplicado_institucion_curso_es_409(client, admin_headers, carrera_test):
    _crear(client, admin_headers, [carrera_test.id])

    r = client.post(
        "/talentotech/",
        json=_payload([carrera_test.id], descripcion="Otra descripción"),
        headers=admin_headers,
    )

    assert r.status_code == 409, r.text


# ───────────────────────── Consultas por carrera / categoría ─────────────────────────


def test_get_by_carrera_incluye_explicito_y_wildcard(
    client, admin_headers, carrera_test, db_session
):
    otra = _crear_carrera(db_session, "Otra Carrera", carrera_test.ifts_id)

    explicito = _crear(
        client, admin_headers, [carrera_test.id], nombre_curso="Curso explícito"
    )
    _crear(client, admin_headers, [otra.id], nombre_curso="Curso de otra")
    wildcard = _crear(client, admin_headers, todas_las_carreras=True, nombre_curso="Wildcard")

    r = client.get(f"/talentotech/carrera/{carrera_test.id}", params={"per_page": 50})

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 2
    assert {c["id"] for c in body["items"]} == {explicito["id"], wildcard["id"]}


def test_get_by_carrera_inexistente_devuelve_vacio(client, admin_headers):
    _crear(client, admin_headers, todas_las_carreras=True, nombre_curso="Wildcard")

    r = client.get("/talentotech/carrera/999999", params={"per_page": 50})

    assert r.status_code == 200, r.text
    assert r.json()["total"] == 0


def test_get_by_categoria(client, admin_headers, carrera_test):
    it = _crear(client, admin_headers, [carrera_test.id], nombre_curso="Curso IT")
    _crear(client, admin_headers, [carrera_test.id], nombre_curso="Curso Data", categoria="Data")

    r = client.get("/talentotech/categoria/IT", params={"per_page": 50})

    assert r.status_code == 200, r.text
    assert [c["id"] for c in r.json()["items"]] == [it["id"]]


def test_orden_por_nombre_curso_case_insensitive(client, admin_headers, carrera_test):
    _crear(client, admin_headers, [carrera_test.id], nombre_curso="zeta")
    _crear(client, admin_headers, [carrera_test.id], nombre_curso="Alfa")

    items = client.get("/talentotech/", params={"per_page": 50}).json()["items"]
    nombres = [c["nombre_curso"] for c in items]

    assert nombres.index("Alfa") < nombres.index("zeta")


# ───────────────────────── Update / delete ─────────────────────────


def test_put_reemplaza_las_carreras(client, admin_headers, carrera_test, db_session):
    otra = _crear_carrera(db_session, "Otra Carrera", carrera_test.ifts_id)
    curso = _crear(client, admin_headers, [carrera_test.id])

    r = client.put(
        f"/talentotech/{curso['id']}",
        json=_payload([otra.id], nombre_curso=curso["nombre_curso"]),
        headers=admin_headers,
    )

    assert r.status_code == 200, r.text
    assert _ids_carreras(r.json()) == [otra.id]


def test_put_a_wildcard_limpia_carreras(client, admin_headers, carrera_test):
    curso = _crear(client, admin_headers, [carrera_test.id])

    r = client.put(
        f"/talentotech/{curso['id']}",
        json=_payload(todas_las_carreras=True, nombre_curso=curso["nombre_curso"]),
        headers=admin_headers,
    )

    assert r.status_code == 200, r.text
    assert r.json()["todas_las_carreras"] is True
    assert r.json()["carreras"] == []


def test_delete_elimina_curso_y_asociaciones(client, admin_headers, carrera_test):
    curso = _crear(client, admin_headers, [carrera_test.id])

    r = client.delete(f"/talentotech/{curso['id']}", headers=admin_headers)

    assert r.status_code == 204, r.text
    assert client.get(f"/talentotech/{curso['id']}").status_code == 404


def test_estudiante_no_puede_crear(client, auth_headers):
    r = client.post("/talentotech/", json=_payload([1]), headers=auth_headers)

    assert r.status_code == 403, r.text
