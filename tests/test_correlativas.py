"""
tests/test_correlativas.py

Tests de integración para el alta y baja de correlatividades
(POST/DELETE /materias/correlativas), Sprint 7 - persona C.

Son endpoints solo-admin (Depends(require_admin)); los casos de autorización
por rol (estudiante -> 403, sin token -> 401) siguen el mismo criterio que
tests/test_materias.py.
"""

from app.features.materias.model import Materia


def _crear_materia(db_session, carrera_id, codigo, nombre="Materia"):
    materia = Materia(
        carrera_id=carrera_id, nombre=nombre, codigo=codigo, anio=1, cuatrimestre=1
    )
    db_session.add(materia)
    db_session.commit()
    db_session.refresh(materia)
    return materia


# ========== Alta ==========


def test_crear_correlativa_con_auth(client, admin_headers, db_session, carrera_test):
    materia = _crear_materia(db_session, carrera_test.id, "PROG2", "Programación II")
    requiere = _crear_materia(db_session, carrera_test.id, "PROG1", "Programación I")

    response = client.post(
        "/materias/correlativas",
        json={"materia_id": materia.id, "requiere_id": requiere.id},
        headers=admin_headers,
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["materia_id"] == materia.id
    assert data["requiere_id"] == requiere.id
    assert data["requiere"]["id"] == requiere.id
    assert data["requiere"]["codigo"] == "PROG1"


def test_crear_correlativa_sin_auth(client, db_session, carrera_test):
    materia = _crear_materia(db_session, carrera_test.id, "PROG2")
    requiere = _crear_materia(db_session, carrera_test.id, "PROG1")

    response = client.post(
        "/materias/correlativas",
        json={"materia_id": materia.id, "requiere_id": requiere.id},
    )

    assert response.status_code == 401


def test_crear_correlativa_como_estudiante(client, auth_headers, db_session, carrera_test):
    materia = _crear_materia(db_session, carrera_test.id, "PROG2")
    requiere = _crear_materia(db_session, carrera_test.id, "PROG1")

    response = client.post(
        "/materias/correlativas",
        json={"materia_id": materia.id, "requiere_id": requiere.id},
        headers=auth_headers,
    )

    assert response.status_code == 403


def test_crear_correlativa_materia_inexistente(client, admin_headers, db_session, carrera_test):
    requiere = _crear_materia(db_session, carrera_test.id, "PROG1")

    response = client.post(
        "/materias/correlativas",
        json={"materia_id": 99999, "requiere_id": requiere.id},
        headers=admin_headers,
    )

    assert response.status_code == 404


def test_crear_correlativa_requiere_inexistente(client, admin_headers, db_session, carrera_test):
    materia = _crear_materia(db_session, carrera_test.id, "PROG2")

    response = client.post(
        "/materias/correlativas",
        json={"materia_id": materia.id, "requiere_id": 99999},
        headers=admin_headers,
    )

    assert response.status_code == 404


def test_crear_correlativa_autorreferencia(client, admin_headers, db_session, carrera_test):
    materia = _crear_materia(db_session, carrera_test.id, "PROG1")

    response = client.post(
        "/materias/correlativas",
        json={"materia_id": materia.id, "requiere_id": materia.id},
        headers=admin_headers,
    )

    # La rechaza el schema (422), antes de tocar la base.
    assert response.status_code == 422


def test_crear_correlativa_duplicada(client, admin_headers, db_session, carrera_test):
    materia = _crear_materia(db_session, carrera_test.id, "PROG2")
    requiere = _crear_materia(db_session, carrera_test.id, "PROG1")
    payload = {"materia_id": materia.id, "requiere_id": requiere.id}

    primera = client.post("/materias/correlativas", json=payload, headers=admin_headers)
    assert primera.status_code == 201

    segunda = client.post("/materias/correlativas", json=payload, headers=admin_headers)
    assert segunda.status_code == 409


def test_crear_correlativa_ciclo_directo(client, admin_headers, db_session, carrera_test):
    """A requiere B; intentar que B requiera A (ciclo de 2) debe fallar."""
    a = _crear_materia(db_session, carrera_test.id, "A")
    b = _crear_materia(db_session, carrera_test.id, "B")

    primera = client.post(
        "/materias/correlativas",
        json={"materia_id": a.id, "requiere_id": b.id},
        headers=admin_headers,
    )
    assert primera.status_code == 201

    ciclo = client.post(
        "/materias/correlativas",
        json={"materia_id": b.id, "requiere_id": a.id},
        headers=admin_headers,
    )
    assert ciclo.status_code == 409


def test_crear_correlativa_ciclo_indirecto(client, admin_headers, db_session, carrera_test):
    """A requiere B, B requiere C; intentar que C requiera A (ciclo de 3) debe fallar."""
    a = _crear_materia(db_session, carrera_test.id, "A")
    b = _crear_materia(db_session, carrera_test.id, "B")
    c = _crear_materia(db_session, carrera_test.id, "C")

    r1 = client.post(
        "/materias/correlativas",
        json={"materia_id": a.id, "requiere_id": b.id},
        headers=admin_headers,
    )
    assert r1.status_code == 201

    r2 = client.post(
        "/materias/correlativas",
        json={"materia_id": b.id, "requiere_id": c.id},
        headers=admin_headers,
    )
    assert r2.status_code == 201

    ciclo = client.post(
        "/materias/correlativas",
        json={"materia_id": c.id, "requiere_id": a.id},
        headers=admin_headers,
    )
    assert ciclo.status_code == 409


def test_crear_correlativa_sin_ciclo_no_se_bloquea(client, admin_headers, db_session, carrera_test):
    """Dos materias que comparten un mismo requisito no forman ciclo: debe permitirse."""
    a = _crear_materia(db_session, carrera_test.id, "A")
    b = _crear_materia(db_session, carrera_test.id, "B")
    base = _crear_materia(db_session, carrera_test.id, "BASE")

    r1 = client.post(
        "/materias/correlativas",
        json={"materia_id": a.id, "requiere_id": base.id},
        headers=admin_headers,
    )
    assert r1.status_code == 201

    r2 = client.post(
        "/materias/correlativas",
        json={"materia_id": b.id, "requiere_id": base.id},
        headers=admin_headers,
    )
    assert r2.status_code == 201


# ========== Baja ==========


def test_eliminar_correlativa(client, admin_headers, db_session, carrera_test):
    materia = _crear_materia(db_session, carrera_test.id, "PROG2")
    requiere = _crear_materia(db_session, carrera_test.id, "PROG1")

    creada = client.post(
        "/materias/correlativas",
        json={"materia_id": materia.id, "requiere_id": requiere.id},
        headers=admin_headers,
    )
    assert creada.status_code == 201
    correlativa_id = creada.json()["id"]

    response = client.delete(
        f"/materias/correlativas/{correlativa_id}", headers=admin_headers
    )
    assert response.status_code == 204

    # Ya no aparece en el listado de correlativas de la materia.
    listado = client.get(f"/materias/correlativas/{materia.id}")
    assert listado.status_code == 200
    assert listado.json()["total"] == 0


def test_eliminar_correlativa_inexistente(client, admin_headers):
    response = client.delete("/materias/correlativas/99999", headers=admin_headers)
    assert response.status_code == 404


def test_eliminar_correlativa_sin_auth(client, admin_headers, db_session, carrera_test):
    materia = _crear_materia(db_session, carrera_test.id, "PROG2")
    requiere = _crear_materia(db_session, carrera_test.id, "PROG1")

    creada = client.post(
        "/materias/correlativas",
        json={"materia_id": materia.id, "requiere_id": requiere.id},
        headers=admin_headers,
    )
    assert creada.status_code == 201

    response = client.delete(f"/materias/correlativas/{creada.json()['id']}")
    assert response.status_code == 401


def test_eliminar_correlativa_como_estudiante(
    client, admin_headers, auth_headers, db_session, carrera_test
):
    materia = _crear_materia(db_session, carrera_test.id, "PROG2")
    requiere = _crear_materia(db_session, carrera_test.id, "PROG1")

    creada = client.post(
        "/materias/correlativas",
        json={"materia_id": materia.id, "requiere_id": requiere.id},
        headers=admin_headers,
    )
    assert creada.status_code == 201

    response = client.delete(
        f"/materias/correlativas/{creada.json()['id']}", headers=auth_headers
    )
    assert response.status_code == 403
