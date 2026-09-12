"""
tests/test_materias.py

Tests de integración para el CRUD de Materias/Carreras.

Los endpoints de escritura de Materias y Carreras son solo-admin
(Depends(require_admin)), así que estos tests usan el fixture `admin_headers`.
Los casos de autorización por rol (estudiante -> 403, sin token -> 401)
viven en tests/test_authorization.py.
"""

# ========== Carreras ==========


def test_crear_carrera_con_auth(client, admin_headers, db_session):
    # Necesitamos que exista un IFTS antes de crear la carrera (FK).
    from app.features.materias.model import IFTS

    ifts = IFTS(nombre="IFTS N°1", ubicacion="CABA")
    db_session.add(ifts)
    db_session.commit()
    db_session.refresh(ifts)

    payload = {
        "nombre": "Tecnicatura en Análisis de Sistemas",
        "duracion_cuatrimestres": 6,
        "ifts_id": ifts.id,
    }

    response = client.post("/materias/carreras", json=payload, headers=admin_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == payload["nombre"]
    assert data["duracion_cuatrimestres"] == 6


def test_crear_carrera_sin_auth(client, db_session):
    from app.features.materias.model import IFTS

    ifts = IFTS(nombre="IFTS N°1", ubicacion="CABA")
    db_session.add(ifts)
    db_session.commit()
    db_session.refresh(ifts)

    payload = {
        "nombre": "Tecnicatura sin auth",
        "duracion_cuatrimestres": 4,
        "ifts_id": ifts.id,
    }

    response = client.post("/materias/carreras", json=payload)

    assert response.status_code == 401


def test_actualizar_carrera(client, admin_headers, carrera_test):
    payload = {"nombre": "Tecnicatura en Programación (actualizada)"}

    response = client.put(
        f"/materias/carreras/{carrera_test.id}",
        json=payload,
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["nombre"] == payload["nombre"]
    # Campo no enviado: debe conservar el valor original
    assert data["duracion_cuatrimestres"] == carrera_test.duracion_cuatrimestres


def test_actualizar_carrera_inexistente(client, admin_headers):
    response = client.put(
        "/materias/carreras/99999",
        json={"nombre": "No existe"},
        headers=admin_headers,
    )

    assert response.status_code == 404


def test_eliminar_carrera(client, admin_headers, carrera_test):
    response = client.delete(
        f"/materias/carreras/{carrera_test.id}", headers=admin_headers
    )
    assert response.status_code == 204

    # Verificamos que ya no se puede volver a actualizar (no existe más)
    response = client.put(
        f"/materias/carreras/{carrera_test.id}",
        json={"nombre": "Fantasma"},
        headers=admin_headers,
    )
    assert response.status_code == 404


def test_eliminar_carrera_inexistente(client, admin_headers):
    response = client.delete("/materias/carreras/99999", headers=admin_headers)

    assert response.status_code == 404


# ========== Materias ==========


def test_crear_materia(client, admin_headers, carrera_test):
    payload = {
        "carrera_id": carrera_test.id,
        "nombre": "Programación I",
        "codigo": "PROG1",
        "anio": 1,
        "cuatrimestre": 1,
    }

    response = client.post("/materias/", json=payload, headers=admin_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["codigo"] == "PROG1"


def test_crear_materia_codigo_duplicado(client, admin_headers, carrera_test):
    payload = {
        "carrera_id": carrera_test.id,
        "nombre": "Programación I",
        "codigo": "PROG1",
        "anio": 1,
        "cuatrimestre": 1,
    }

    primera = client.post("/materias/", json=payload, headers=admin_headers)
    assert primera.status_code == 201

    segunda = client.post("/materias/", json=payload, headers=admin_headers)

    assert segunda.status_code == 409


# ========== Búsqueda de Materias ==========


def test_buscar_materia_por_nombre(client, db_session, carrera_test):
    from app.features.materias.model import Materia

    materia = Materia(
        carrera_id=carrera_test.id,
        nombre="Programación I",
        codigo="PROG1",
        anio=1,
        cuatrimestre=1,
    )
    db_session.add(materia)
    db_session.commit()
    db_session.refresh(materia)

    response = client.get(f"/materias/buscar?q=Programación")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == materia.id
    assert data["items"][0]["nombre"] == materia.nombre


def test_buscar_materia_por_codigo(client, db_session, carrera_test):
    from app.features.materias.model import Materia

    materia = Materia(
        carrera_id=carrera_test.id,
        nombre="Programación II",
        codigo="PROG2",
        anio=2,
        cuatrimestre=1,
    )
    db_session.add(materia)
    db_session.commit()
    db_session.refresh(materia)

    response = client.get(f"/materias/buscar?q=PROG2")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == materia.id
    assert data["items"][0]["codigo"] == materia.codigo


def test_buscar_materia_con_filtro_anio(client, db_session, carrera_test):
    from app.features.materias.model import Materia

    materia_matching = Materia(
        carrera_id=carrera_test.id,
        nombre="Programación I",
        codigo="PROG1",
        anio=1,
        cuatrimestre=1,
    )
    db_session.add(materia_matching)
    db_session.commit()
    db_session.refresh(materia_matching)

    materia_other = Materia(
        carrera_id=carrera_test.id,
        nombre="Programación I",
        codigo="PROG2",
        anio=2,
        cuatrimestre=1,
    )
    db_session.add(materia_other)
    db_session.commit()
    db_session.refresh(materia_other)

    response = client.get(
        f"/materias/buscar?q=Programación&anio=1"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == materia_matching.id
    assert data["items"][0]["anio"] == 1


def test_buscar_materia_con_filtro_cuatrimestre(client, db_session, carrera_test):
    from app.features.materias.model import Materia

    materia_matching = Materia(
        carrera_id=carrera_test.id,
        nombre="Programación I",
        codigo="PROG1",
        anio=1,
        cuatrimestre=1,
    )
    db_session.add(materia_matching)
    db_session.commit()
    db_session.refresh(materia_matching)

    materia_other = Materia(
        carrera_id=carrera_test.id,
        nombre="Programación I",
        codigo="PROG2",
        anio=1,
        cuatrimestre=2,
    )
    db_session.add(materia_other)
    db_session.commit()
    db_session.refresh(materia_other)

    response = client.get(
        f"/materias/buscar?q=Programación&cuatrimestre=1"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == materia_matching.id
    assert data["items"][0]["cuatrimestre"] == 1


def test_buscar_materia_sin_resultados(client, db_session, carrera_test):
    from app.features.materias.model import Materia

    materia = Materia(
        carrera_id=carrera_test.id,
        nombre="Programación I",
        codigo="PROG1",
        anio=1,
        cuatrimestre=1,
    )
    db_session.add(materia)
    db_session.commit()
    db_session.refresh(materia)

    response = client.get("/materias/buscar?q=Matemática")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


# ========== Detalle individual (Sprint 2 - contrato para el front) ==========


def _crear_materia(db_session, carrera_id, codigo="PROG1", nombre="Programación I"):
    from app.features.materias.model import Materia

    materia = Materia(
        carrera_id=carrera_id, nombre=nombre, codigo=codigo, anio=1, cuatrimestre=1
    )
    db_session.add(materia)
    db_session.commit()
    db_session.refresh(materia)
    return materia


def test_get_carrera_detalle(client, carrera_test):
    r = client.get(f"/materias/carreras/{carrera_test.id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == carrera_test.id
    assert data["nombre"] == carrera_test.nombre
    assert data["ifts_id"] == carrera_test.ifts_id


def test_get_carrera_detalle_inexistente(client):
    r = client.get("/materias/carreras/99999")
    assert r.status_code == 404
    assert set(r.json().keys()) == {"detail"}


def test_get_materia_detalle(client, db_session, carrera_test):
    materia = _crear_materia(db_session, carrera_test.id, codigo="PROG1")
    r = client.get(f"/materias/{materia.id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == materia.id
    assert data["codigo"] == "PROG1"
    assert data["carrera_id"] == carrera_test.id


def test_get_materia_detalle_inexistente(client):
    r = client.get("/materias/99999")
    assert r.status_code == 404
    assert set(r.json().keys()) == {"detail"}


def test_detalle_es_lectura_publica(client, db_session, carrera_test):
    """Sin token → 200 (no 401)."""
    materia = _crear_materia(db_session, carrera_test.id, codigo="BD1", nombre="Base de Datos")
    assert client.get(f"/materias/{materia.id}").status_code == 200
    assert client.get(f"/materias/carreras/{carrera_test.id}").status_code == 200


def test_get_materia_no_colisiona_con_rutas_especificas(client, carrera_test):
    """El comodín GET /{materia_id} no debe tapar /carreras, /buscar, /carrera/{id}."""
    assert client.get("/materias/carreras").status_code == 200
    assert client.get("/materias/buscar?q=x").status_code == 200
    assert client.get(f"/materias/carrera/{carrera_test.id}").status_code == 200


# ========== Estado y nota_final derivados de una cursada ==========
#
# Regla: la promoción exime de rendir el final, así que se decide por los
# PARCIALES, no por el examen: ambos parciales `>= 7` -> "promocionada", y
# `nota_final` (calculada, no se manda) es el promedio de los dos parciales.
# Si no promocionó y se rindió `examen_final`: `>= 4` "aprobada" (nota_final =
# examen_final), `< 4` "desaprobada". Si no promocionó y no hay examen_final:
# "pendiente". `cursando=True` manda por sobre cualquier nota cargada. Se
# calcula en la capa de servicio (`service.derivar_estado_cursada` /
# `service.derivar_nota_final`), no en el modelo ni en el schema.


def _cargar_cursada_con_final(client, headers, carrera_id, db_session, examen_final, codigo):
    """Crea una materia + cursada y le carga `examen_final` vía PATCH. Devuelve el item actualizado."""
    materia = _crear_materia(db_session, carrera_id, codigo=codigo)
    creada = client.post(
        "/materias/usuario",
        json={"materia_id": materia.id, "cursando": False},
        headers=headers,
    )
    assert creada.status_code == 201, creada.text

    editada = client.patch(
        f"/materias/cursada/{creada.json()['id']}",
        json={"examen_final": examen_final},
        headers=headers,
    )
    assert editada.status_code == 200, editada.text
    return editada.json()


def _cargar_cursada_con_parciales(
    client, headers, carrera_id, db_session, nota_parcial_1, nota_parcial_2, codigo
):
    """Crea una materia + cursada y le carga ambos parciales vía PATCH."""
    materia = _crear_materia(db_session, carrera_id, codigo=codigo)
    creada = client.post(
        "/materias/usuario",
        json={"materia_id": materia.id, "cursando": False},
        headers=headers,
    )
    assert creada.status_code == 201, creada.text

    editada = client.patch(
        f"/materias/cursada/{creada.json()['id']}",
        json={"nota_parcial_1": nota_parcial_1, "nota_parcial_2": nota_parcial_2},
        headers=headers,
    )
    assert editada.status_code == 200, editada.text
    return editada.json()


def test_estado_cursando_ignora_la_nota(
    client, auth_headers, carrera_test, db_session
):
    materia = _crear_materia(db_session, carrera_test.id, codigo="EST-CUR")
    r = client.post(
        "/materias/usuario",
        json={"materia_id": materia.id, "cursando": True},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["estado"] == "cursando"


def test_estado_pendiente_sin_nota_ni_cursando(
    client, auth_headers, carrera_test, db_session
):
    materia = _crear_materia(db_session, carrera_test.id, codigo="EST-PEND")
    r = client.post(
        "/materias/usuario",
        json={"materia_id": materia.id, "cursando": False},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["estado"] == "pendiente"


def test_estado_desaprobada_con_nota_menor_a_4(
    client, auth_headers, carrera_test, db_session
):
    item = _cargar_cursada_con_final(
        client, auth_headers, carrera_test.id, db_session, examen_final=3, codigo="EST-DES"
    )
    assert item["estado"] == "desaprobada"


def test_estado_aprobada_en_el_limite_de_4(
    client, auth_headers, carrera_test, db_session
):
    item = _cargar_cursada_con_final(
        client, auth_headers, carrera_test.id, db_session, examen_final=4, codigo="EST-AP4"
    )
    assert item["estado"] == "aprobada"


def test_estado_aprobada_con_nota_intermedia(
    client, auth_headers, carrera_test, db_session
):
    item = _cargar_cursada_con_final(
        client, auth_headers, carrera_test.id, db_session, examen_final=6, codigo="EST-AP6"
    )
    assert item["estado"] == "aprobada"


def test_estado_promociona_con_ambos_parciales_en_el_limite_de_7(
    client, auth_headers, carrera_test, db_session
):
    item = _cargar_cursada_con_parciales(
        client, auth_headers, carrera_test.id, db_session,
        nota_parcial_1=7, nota_parcial_2=7, codigo="EST-PR7",
    )
    assert item["estado"] == "promocionada"
    assert item["nota_final"] == 7  # promedio de los parciales
    assert item["examen_final"] is None  # nunca lo rindió


def test_estado_promociona_con_parciales_altos(
    client, auth_headers, carrera_test, db_session
):
    item = _cargar_cursada_con_parciales(
        client, auth_headers, carrera_test.id, db_session,
        nota_parcial_1=10, nota_parcial_2=8, codigo="EST-PR10",
    )
    assert item["estado"] == "promocionada"
    assert item["nota_final"] == 9  # (10+8)/2


def test_estado_no_promociona_si_un_solo_parcial_es_alto(
    client, auth_headers, carrera_test, db_session
):
    """Falta el otro parcial >= 7: no promociona, depende del examen_final como siempre."""
    item = _cargar_cursada_con_parciales(
        client, auth_headers, carrera_test.id, db_session,
        nota_parcial_1=9, nota_parcial_2=5, codigo="EST-NOPR",
    )
    assert item["estado"] == "pendiente"  # todavía no rindió el final

    editada = client.patch(
        f"/materias/cursada/{item['id']}", json={"examen_final": 6}, headers=auth_headers
    )
    assert editada.status_code == 200, editada.text
    assert editada.json()["estado"] == "aprobada"
    assert editada.json()["nota_final"] == 6


def test_promocion_ignora_examen_final_viejo(
    client, auth_headers, carrera_test, db_session
):
    """Reproduce el caso reportado: cargás un final (queda desaprobada), después
    subís los dos parciales a >= 7 sin tocar el final -> pasa a promocionada, y
    nota_final (calculada) ya no mira ese examen_final viejo, no queda una nota
    inconsistente."""
    item = _cargar_cursada_con_final(
        client, auth_headers, carrera_test.id, db_session, examen_final=3, codigo="EST-RESET"
    )
    assert item["estado"] == "desaprobada"
    assert item["nota_final"] == 3

    editada = client.patch(
        f"/materias/cursada/{item['id']}",
        json={"nota_parcial_1": 8, "nota_parcial_2": 9},
        headers=auth_headers,
    )
    assert editada.status_code == 200, editada.text
    assert editada.json()["estado"] == "promocionada"
    assert editada.json()["nota_final"] == 8.5  # (8+9)/2, ignora el examen_final=3 viejo


def test_crear_cursada_con_parciales_altos_ignora_examen_final(
    client, auth_headers, carrera_test, db_session
):
    """Si se manda examen_final junto con parciales que promocionan, se ignora igual."""
    materia = _crear_materia(db_session, carrera_test.id, codigo="EST-CREATEPROMO")
    r = client.post(
        "/materias/usuario",
        json={
            "materia_id": materia.id,
            "cursando": False,
            "nota_parcial_1": 8,
            "nota_parcial_2": 8,
            "examen_final": 5,
        },
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["estado"] == "promocionada"
    assert r.json()["nota_final"] == 8  # promedio de los parciales, no el examen_final=5


def test_estado_viaja_en_el_listado_de_mis_cursadas(
    client, auth_headers, usuario_registrado, carrera_test, db_session
):
    """El GET paginado de /materias/usuario/{id} también trae `estado` calculado."""
    _cargar_cursada_con_final(
        client, auth_headers, carrera_test.id, db_session, examen_final=2, codigo="EST-LIST"
    )
    mi_id = usuario_registrado["response"]["id"]
    r = client.get(f"/materias/usuario/{mi_id}", headers=auth_headers)
    assert r.status_code == 200, r.text
    estados = {item["materia_id"]: item["estado"] for item in r.json()["items"]}
    assert "desaprobada" in estados.values()


def test_promedio_computa_promocionada_con_el_promedio_de_los_parciales(
    client, auth_headers, usuario_registrado, carrera_test, db_session
):
    """Una promocionada no tiene nota_final: al promedio general aporta el
    promedio de sus dos parciales, no un None que la deje afuera de la cuenta."""
    _cargar_cursada_con_parciales(
        client, auth_headers, carrera_test.id, db_session,
        nota_parcial_1=10, nota_parcial_2=8, codigo="PROM-PROMO",  # promedia 9
    )
    _cargar_cursada_con_final(
        client, auth_headers, carrera_test.id, db_session,
        examen_final=6, codigo="PROM-AP",
    )

    mi_id = usuario_registrado["response"]["id"]
    r = client.get(f"/materias/promedio/{mi_id}", headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["materias_computadas"] == 2
    assert data["promedio"] == 7.5  # (9 + 6) / 2
