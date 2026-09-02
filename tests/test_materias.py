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
