"""Cobertura del contrato extendido de convenios (RF-28…RF-36 / AC-1…AC-14)."""


def _payload(carrera_ids=None, **overrides) -> dict:
    data = {
        "institucion": "Universidad Nacional",
        "carrera_destino": "Licenciatura en Sistemas",
        "descripcion": "Articulación con reconocimiento de materias",
        "link_info": "https://ejemplo.com/convenio",
    }
    if carrera_ids is not None:
        data["carrera_ids"] = carrera_ids
    data.update(overrides)
    return data


def _crear(client, admin_headers, carrera_ids=None, **overrides) -> dict:
    r = client.post(
        "/convenios/", json=_payload(carrera_ids, **overrides), headers=admin_headers
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


def _ids_carreras(convenio: dict) -> list[int]:
    return [carrera["id"] for carrera in convenio["carreras"]]


# ────────────────────────── PATCH parcial (AC-1) ──────────────────────────


def test_patch_parcial_solo_modifica_campos_presentes(client, admin_headers, carrera_test):
    creado = _crear(client, admin_headers, [carrera_test.id])

    r = client.patch(
        f"/convenios/{creado['id']}",
        json={"descripcion": "Descripción nueva"},
        headers=admin_headers,
    )

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["descripcion"] == "Descripción nueva"
    assert body["institucion"] == creado["institucion"]
    assert body["carrera_destino"] == creado["carrera_destino"]
    assert body["link_info"] == creado["link_info"]
    assert body["todas_las_carreras"] is False
    assert _ids_carreras(body) == [carrera_test.id]
    assert body["id"] == creado["id"]


def test_patch_body_vacio_devuelve_200_sin_cambios(client, admin_headers, carrera_test):
    creado = _crear(client, admin_headers, [carrera_test.id])

    r = client.patch(f"/convenios/{creado['id']}", json={}, headers=admin_headers)

    assert r.status_code == 200, r.text
    assert r.json() == creado


def test_patch_sin_token_401_y_estudiante_403(
    client, admin_headers, auth_headers, carrera_test
):
    creado = _crear(client, admin_headers, [carrera_test.id])
    url = f"/convenios/{creado['id']}"

    assert client.patch(url, json={"descripcion": "x"}).status_code == 401
    assert (
        client.patch(url, json={"descripcion": "x"}, headers=auth_headers).status_code
        == 403
    )


def test_patch_id_inexistente_404(client, admin_headers):
    r = client.patch("/convenios/999999", json={"descripcion": "x"}, headers=admin_headers)
    assert r.status_code == 404


# ────────────────────────── Búsqueda ?q= (AC-2) ──────────────────────────


def test_q_busca_case_insensitive_en_los_tres_campos(client, admin_headers, carrera_test):
    _crear(
        client,
        admin_headers,
        [carrera_test.id],
        institucion="Universidad Tecnologica",
        carrera_destino="Ingeniería",
        descripcion="Convenio marco",
    )
    _crear(
        client,
        admin_headers,
        [carrera_test.id],
        institucion="Instituto Oeste",
        carrera_destino="Tecnicatura en Datos",
        descripcion="Pasantías rentadas",
    )

    for q, esperado in [
        ("TECNOLOGICA", "Universidad Tecnologica"),
        ("datos", "Instituto Oeste"),
        ("pasantías", "Instituto Oeste"),
        ("universidad", "Universidad Tecnologica"),
    ]:
        r = client.get("/convenios/", params={"q": q})
        assert r.status_code == 200, r.text
        items = r.json()["items"]
        assert len(items) == 1, f"q={q} devolvió {items}"
        assert items[0]["institucion"] == esperado


def test_q_vacio_o_ausente_no_filtra(client, admin_headers, carrera_test):
    _crear(client, admin_headers, [carrera_test.id], institucion="A")
    _crear(client, admin_headers, [carrera_test.id], institucion="B")

    sin_q = client.get("/convenios/").json()
    q_vacio = client.get("/convenios/", params={"q": ""}).json()
    q_espacios = client.get("/convenios/", params={"q": "   "}).json()

    assert sin_q["total"] == 2
    assert q_vacio["total"] == 2
    assert q_espacios["total"] == 2


def test_q_se_aplica_antes_de_paginar(client, admin_headers, carrera_test):
    _crear(client, admin_headers, [carrera_test.id], institucion="Universidad Uno", carrera_destino="A")
    _crear(client, admin_headers, [carrera_test.id], institucion="Universidad Dos", carrera_destino="B")
    _crear(client, admin_headers, [carrera_test.id], institucion="Instituto Tres", carrera_destino="C")

    body = client.get(
        "/convenios/", params={"q": "universidad", "page": 1, "per_page": 1}
    ).json()

    assert body["total"] == 2
    assert body["total_pages"] == 2
    assert len(body["items"]) == 1


def test_q_funciona_en_listado_por_carrera(client, admin_headers, carrera_test):
    _crear(client, admin_headers, [carrera_test.id], institucion="Universidad Uno")
    _crear(client, admin_headers, [carrera_test.id], institucion="Instituto Dos")

    r = client.get(
        f"/convenios/carrera/{carrera_test.id}", params={"q": "universidad"}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["institucion"] == "Universidad Uno"


# ────────────────── Carreras inexistentes y duplicados (AC-3/AC-4) ──────────────────


def test_post_con_carreras_inexistentes_da_422_con_la_lista(client, admin_headers):
    r = client.post(
        "/convenios/", json=_payload([999998, 999999]), headers=admin_headers
    )

    assert r.status_code == 422, r.text
    detail = r.json()["detail"]
    assert "999998" in detail and "999999" in detail


def test_post_con_una_carrera_inexistente_da_422_singular(client, admin_headers):
    r = client.post("/convenios/", json=_payload([999999]), headers=admin_headers)

    assert r.status_code == 422, r.text
    assert "No existe la carrera 999999" == r.json()["detail"]


def test_put_con_carrera_inexistente_da_422(client, admin_headers, carrera_test):
    creado = _crear(client, admin_headers, [carrera_test.id])

    r = client.put(
        f"/convenios/{creado['id']}",
        json=_payload([999999]),
        headers=admin_headers,
    )

    assert r.status_code == 422, r.text
    actual = client.get(f"/convenios/{creado['id']}").json()
    assert _ids_carreras(actual) == [carrera_test.id]


def test_patch_con_carrera_inexistente_da_422(client, admin_headers, carrera_test):
    creado = _crear(client, admin_headers, [carrera_test.id])

    r = client.patch(
        f"/convenios/{creado['id']}",
        json={"carrera_ids": [999999]},
        headers=admin_headers,
    )

    assert r.status_code == 422, r.text
    actual = client.get(f"/convenios/{creado['id']}").json()
    assert _ids_carreras(actual) == [carrera_test.id]


def test_post_duplicado_da_409(client, admin_headers, carrera_test):
    _crear(client, admin_headers, [carrera_test.id])

    r = client.post(
        "/convenios/", json=_payload([carrera_test.id]), headers=admin_headers
    )

    assert r.status_code == 409, r.text


def test_post_duplicado_con_otras_carreras_da_409(client, admin_headers, carrera_test, db_session):
    c2 = _crear_carrera(db_session, "Otra Carrera", carrera_test.ifts_id)
    _crear(client, admin_headers, [carrera_test.id])

    r = client.post("/convenios/", json=_payload([c2.id]), headers=admin_headers)

    assert r.status_code == 409, r.text


def test_post_duplicado_tras_strip_da_409(client, admin_headers, carrera_test):
    _crear(client, admin_headers, [carrera_test.id], institucion="Universidad Nacional")

    r = client.post(
        "/convenios/",
        json=_payload([carrera_test.id], institucion="  Universidad Nacional  "),
        headers=admin_headers,
    )

    assert r.status_code == 409, r.text


def test_dos_convenios_distintos_dan_201(client, admin_headers, carrera_test):
    _crear(client, admin_headers, [carrera_test.id], carrera_destino="Licenciatura A")
    _crear(client, admin_headers, [carrera_test.id], carrera_destino="Licenciatura B")


def test_patch_que_colisiona_da_409(client, admin_headers, carrera_test):
    a = _crear(client, admin_headers, [carrera_test.id], institucion="Universidad A")
    b = _crear(
        client,
        admin_headers,
        [carrera_test.id],
        institucion="Universidad B",
        carrera_destino=a["carrera_destino"],
    )

    r = client.patch(
        f"/convenios/{b['id']}",
        json={"institucion": "Universidad A"},
        headers=admin_headers,
    )

    assert r.status_code == 409, r.text


# ───────────────────────── Orden estable (AC-5) ─────────────────────────


def test_orden_institucion_asc_id_asc_es_estable(client, admin_headers, carrera_test):
    _crear(client, admin_headers, [carrera_test.id], institucion="Zeta", carrera_destino="Z1")
    alfa_1 = _crear(client, admin_headers, [carrera_test.id], institucion="Alfa", carrera_destino="A2")
    _crear(client, admin_headers, [carrera_test.id], institucion="Beta", carrera_destino="B1")
    alfa_2 = _crear(client, admin_headers, [carrera_test.id], institucion="Alfa", carrera_destino="A1")

    primera = client.get("/convenios/", params={"per_page": 50}).json()["items"]
    segunda = client.get("/convenios/", params={"per_page": 50}).json()["items"]

    claves = [(c["institucion"], c["id"]) for c in primera]
    assert claves == sorted(claves)
    assert [c["id"] for c in primera] == [c["id"] for c in segunda]

    ids_alfa = [c["id"] for c in primera if c["institucion"] == "Alfa"]
    assert ids_alfa == sorted([alfa_1["id"], alfa_2["id"]])

    por_carrera = client.get(
        f"/convenios/carrera/{carrera_test.id}", params={"per_page": 50}
    ).json()["items"]
    claves_carrera = [(c["institucion"], c["id"]) for c in por_carrera]
    assert claves_carrera == sorted(claves_carrera)


def test_orden_institucion_es_case_insensitive(client, admin_headers, carrera_test):
    """D19: 'universidad ...' debe ordenar junto a las mayúsculas, no antes de 'Z'."""
    _crear(client, admin_headers, [carrera_test.id], institucion="Zeta")
    _crear(client, admin_headers, [carrera_test.id], institucion="universidad de Buenos Aires")

    items = client.get("/convenios/", params={"per_page": 50}).json()["items"]
    instituciones = [c["institucion"] for c in items]

    assert instituciones.index("universidad de Buenos Aires") < instituciones.index("Zeta")


# ───────────────────────── N:M y wildcard (AC-9/AC-10) ─────────────────────────


def test_convenio_m2m_aparece_en_sus_carreras_y_no_en_otras(
    client, admin_headers, carrera_test, db_session
):
    c2 = _crear_carrera(db_session, "Carrera Dos", carrera_test.ifts_id)
    c3 = _crear_carrera(db_session, "Carrera Tres", carrera_test.ifts_id)

    creado = _crear(client, admin_headers, [carrera_test.id, c2.id])
    assert sorted(_ids_carreras(creado)) == sorted([carrera_test.id, c2.id])

    for carrera in (carrera_test, c2):
        body = client.get(f"/convenios/carrera/{carrera.id}").json()
        assert [item["id"] for item in body["items"]] == [creado["id"]]

    body = client.get(f"/convenios/carrera/{c3.id}").json()
    assert body["total"] == 0


def test_wildcard_aparece_en_cualquier_carrera_y_devuelve_carreras_vacias(
    client, admin_headers, carrera_test, db_session
):
    c2 = _crear_carrera(db_session, "Carrera Dos", carrera_test.ifts_id)

    creado = _crear(client, admin_headers, todas_las_carreras=True)
    assert creado["todas_las_carreras"] is True
    assert creado["carreras"] == []

    for carrera in (carrera_test, c2):
        body = client.get(f"/convenios/carrera/{carrera.id}").json()
        assert [item["id"] for item in body["items"]] == [creado["id"]]


def test_carrera_inexistente_devuelve_lista_vacia_aunque_haya_wildcard(
    client, admin_headers, carrera_test
):
    _crear(client, admin_headers, todas_las_carreras=True)

    body = client.get("/convenios/carrera/999999").json()

    assert body["total"] == 0
    assert body["items"] == []


def test_carreras_de_la_respuesta_ordenadas_por_nombre(
    client, admin_headers, carrera_test, db_session
):
    zeta = _crear_carrera(db_session, "Zeta", carrera_test.ifts_id)
    alfa = _crear_carrera(db_session, "Alfa", carrera_test.ifts_id)

    creado = _crear(client, admin_headers, [zeta.id, alfa.id])

    assert [c["nombre"] for c in creado["carreras"]] == ["Alfa", "Zeta"]


def test_dedupe_de_carrera_ids(client, admin_headers, carrera_test, db_session):
    c2 = _crear_carrera(db_session, "Carrera Dos", carrera_test.ifts_id)

    creado = _crear(
        client,
        admin_headers,
        [carrera_test.id, c2.id, carrera_test.id, c2.id],
    )

    assert sorted(_ids_carreras(creado)) == sorted([carrera_test.id, c2.id])


# ───────────────────────── Invariante flag ↔ ids (AC-11/AC-12) ─────────────────────────


def test_post_flag_true_con_ids_da_422(client, admin_headers, carrera_test):
    r = client.post(
        "/convenios/",
        json=_payload([carrera_test.id], todas_las_carreras=True),
        headers=admin_headers,
    )

    assert r.status_code == 422, r.text


def test_post_sin_carreras_ni_flag_da_422(client, admin_headers):
    r = client.post("/convenios/", json=_payload(None), headers=admin_headers)
    assert r.status_code == 422, r.text


def test_patch_flag_true_limpia_las_carreras_explicitas(
    client, admin_headers, carrera_test, db_session
):
    from app.features.recursos.model import ConvenioCarrera

    creado = _crear(client, admin_headers, [carrera_test.id])
    assert db_session.query(ConvenioCarrera).count() == 1

    r = client.patch(
        f"/convenios/{creado['id']}",
        json={"todas_las_carreras": True},
        headers=admin_headers,
    )

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["todas_las_carreras"] is True
    assert body["carreras"] == []
    assert db_session.query(ConvenioCarrera).count() == 0

    # Y ahora aparece en cualquier carrera.
    assert client.get(f"/convenios/carrera/{carrera_test.id}").json()["total"] == 1


def test_patch_flag_false_sin_carreras_previas_da_422(
    client, admin_headers, carrera_test
):
    creado = _crear(client, admin_headers, todas_las_carreras=True)

    r = client.patch(
        f"/convenios/{creado['id']}",
        json={"todas_las_carreras": False},
        headers=admin_headers,
    )

    assert r.status_code == 422, r.text
    actual = client.get(f"/convenios/{creado['id']}").json()
    assert actual["todas_las_carreras"] is True


def test_patch_flag_false_con_carreras_previas_las_conserva(
    client, admin_headers, carrera_test
):
    creado = _crear(client, admin_headers, todas_las_carreras=True)
    client.patch(
        f"/convenios/{creado['id']}",
        json={"todas_las_carreras": False, "carrera_ids": [carrera_test.id]},
        headers=admin_headers,
    )

    r = client.patch(
        f"/convenios/{creado['id']}",
        json={"institucion": "Otra institución"},
        headers=admin_headers,
    )

    assert r.status_code == 200, r.text
    assert _ids_carreras(r.json()) == [carrera_test.id]


def test_patch_carrera_ids_reemplaza_el_conjunto(
    client, admin_headers, carrera_test, db_session
):
    c2 = _crear_carrera(db_session, "Carrera Dos", carrera_test.ifts_id)
    creado = _crear(client, admin_headers, [carrera_test.id])

    r = client.patch(
        f"/convenios/{creado['id']}",
        json={"carrera_ids": [c2.id]},
        headers=admin_headers,
    )

    assert r.status_code == 200, r.text
    assert _ids_carreras(r.json()) == [c2.id]
    assert client.get(f"/convenios/carrera/{carrera_test.id}").json()["total"] == 0
    assert client.get(f"/convenios/carrera/{c2.id}").json()["total"] == 1


def test_patch_flag_true_con_ids_da_422(client, admin_headers, carrera_test):
    creado = _crear(client, admin_headers, [carrera_test.id])

    r = client.patch(
        f"/convenios/{creado['id']}",
        json={"todas_las_carreras": True, "carrera_ids": [carrera_test.id]},
        headers=admin_headers,
    )

    assert r.status_code == 422, r.text


def test_put_reemplaza_carreras(client, admin_headers, carrera_test, db_session):
    c2 = _crear_carrera(db_session, "Carrera Dos", carrera_test.ifts_id)
    creado = _crear(client, admin_headers, [carrera_test.id])

    r = client.put(
        f"/convenios/{creado['id']}",
        json=_payload([c2.id]),
        headers=admin_headers,
    )

    assert r.status_code == 200, r.text
    assert _ids_carreras(r.json()) == [c2.id]


# ───────────────────── Paginación por carrera sin duplicados ─────────────────────


def test_paginacion_por_carrera_no_duplica_filas(
    client, admin_headers, carrera_test, db_session
):
    c2 = _crear_carrera(db_session, "Carrera Dos", carrera_test.ifts_id)
    creados = [
        _crear(
            client,
            admin_headers,
            [carrera_test.id, c2.id],
            institucion=f"Universidad {indice}",
            carrera_destino=f"Destino {indice}",
        )
        for indice in range(3)
    ]

    pagina_1 = client.get(
        f"/convenios/carrera/{carrera_test.id}", params={"page": 1, "per_page": 2}
    ).json()
    pagina_2 = client.get(
        f"/convenios/carrera/{carrera_test.id}", params={"page": 2, "per_page": 2}
    ).json()

    assert pagina_1["total"] == 3
    assert pagina_1["total_pages"] == 2
    ids = [item["id"] for item in pagina_1["items"] + pagina_2["items"]]
    assert sorted(ids) == sorted(item["id"] for item in creados)
    assert len(set(ids)) == 3


def test_delete_limpia_la_tabla_intermedia(
    client, admin_headers, carrera_test, db_session
):
    from app.features.recursos.model import ConvenioCarrera

    creado = _crear(client, admin_headers, [carrera_test.id])
    assert db_session.query(ConvenioCarrera).count() == 1

    r = client.delete(f"/convenios/{creado['id']}", headers=admin_headers)

    assert r.status_code == 204
    assert db_session.query(ConvenioCarrera).count() == 0
