"""
tests/test_authorization.py

Tests de autorización (Integrante 1 - Seguridad y Autenticación).

Cubre:
  - Roles: solo un usuario admin puede crear/editar/eliminar carreras y materias.
    Un estudiante autenticado recibe 403; sin token se recibe 401.
  - Ownership de Recursos: un usuario solo puede editar/eliminar sus propios
    recursos (403 si el recurso es de otro; 401 sin token).
"""

import pytest


# ========== Helpers ==========


def _crear_materia(db_session, carrera_id, codigo="MAT1"):
    from app.features.materias.model import Materia

    materia = Materia(
        carrera_id=carrera_id,
        nombre="Materia de prueba",
        codigo=codigo,
        anio=1,
        cuatrimestre=1,
    )
    db_session.add(materia)
    db_session.commit()
    db_session.refresh(materia)
    return materia


@pytest.fixture
def segundo_estudiante_headers(client, carrera_test) -> dict:
    """Registra y loguea a un segundo estudiante distinto del de `auth_headers`."""
    payload = {
        "nombre": "María López",
        "email": "maria.lopez@example.com",
        "password": "password456",
        "carrera_id": carrera_test.id,
    }
    reg = client.post("/auth/registro", json=payload)
    assert reg.status_code == 201, reg.text

    login = client.post(
        "/auth/login", json={"email": payload["email"], "password": payload["password"]}
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


# ========== Roles: carreras / materias son solo-admin ==========


def test_estudiante_no_puede_crear_carrera(client, auth_headers, carrera_test):
    payload = {
        "nombre": "Carrera prohibida",
        "duracion_cuatrimestres": 4,
        "ifts_id": carrera_test.ifts_id,
    }
    response = client.post("/materias/carreras", json=payload, headers=auth_headers)
    assert response.status_code == 403


def test_estudiante_no_puede_crear_materia(client, auth_headers, carrera_test):
    payload = {
        "carrera_id": carrera_test.id,
        "nombre": "Materia prohibida",
        "codigo": "NOPE1",
        "anio": 1,
        "cuatrimestre": 1,
    }
    response = client.post("/materias/", json=payload, headers=auth_headers)
    assert response.status_code == 403


def test_estudiante_no_puede_eliminar_materia(
    client, auth_headers, carrera_test, db_session
):
    materia = _crear_materia(db_session, carrera_test.id, codigo="DELME")
    response = client.delete(f"/materias/{materia.id}", headers=auth_headers)
    assert response.status_code == 403


def test_admin_puede_crear_materia(client, admin_headers, carrera_test):
    payload = {
        "carrera_id": carrera_test.id,
        "nombre": "Materia autorizada",
        "codigo": "OK1",
        "anio": 1,
        "cuatrimestre": 1,
    }
    response = client.post("/materias/", json=payload, headers=admin_headers)
    assert response.status_code == 201


def test_crear_materia_sin_token(client, carrera_test):
    payload = {
        "carrera_id": carrera_test.id,
        "nombre": "Sin token",
        "codigo": "ANON1",
        "anio": 1,
        "cuatrimestre": 1,
    }
    response = client.post("/materias/", json=payload)
    assert response.status_code == 401


# ========== Ownership de Recursos ==========


def test_usuario_no_puede_editar_recurso_ajeno(
    client, auth_headers, segundo_estudiante_headers, carrera_test, db_session
):
    materia = _crear_materia(db_session, carrera_test.id, codigo="REC1")

    creado = client.post(
        "/recursos/",
        json={
            "titulo": "Apunte de Juan",
            "url": "https://example.com/apunte",
            "descripcion": "Material propio",
            "materia_id": materia.id,
        },
        headers=auth_headers,
    )
    assert creado.status_code == 201, creado.text
    recurso_id = creado.json()["id"]

    # El segundo estudiante intenta modificar el recurso del primero
    response = client.put(
        f"/recursos/{recurso_id}",
        json={
            "titulo": "Editado por otro",
            "url": "https://example.com/hackeado",
            "descripcion": "No debería poder",
            "materia_id": materia.id,
        },
        headers=segundo_estudiante_headers,
    )
    assert response.status_code == 403


def test_dueno_puede_editar_su_recurso(
    client, auth_headers, carrera_test, db_session
):
    materia = _crear_materia(db_session, carrera_test.id, codigo="REC2")

    creado = client.post(
        "/recursos/",
        json={
            "titulo": "Apunte original",
            "url": "https://example.com/original",
            "descripcion": "Material propio",
            "materia_id": materia.id,
        },
        headers=auth_headers,
    )
    assert creado.status_code == 201, creado.text
    recurso_id = creado.json()["id"]

    response = client.put(
        f"/recursos/{recurso_id}",
        json={
            "titulo": "Apunte actualizado",
            "url": "https://example.com/original",
            "descripcion": "Material propio actualizado",
            "materia_id": materia.id,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["titulo"] == "Apunte actualizado"


def test_editar_recurso_sin_token(client, auth_headers, carrera_test, db_session):
    materia = _crear_materia(db_session, carrera_test.id, codigo="REC3")

    creado = client.post(
        "/recursos/",
        json={
            "titulo": "Apunte",
            "url": "https://example.com/x",
            "descripcion": "desc",
            "materia_id": materia.id,
        },
        headers=auth_headers,
    )
    assert creado.status_code == 201, creado.text
    recurso_id = creado.json()["id"]

    response = client.put(
        f"/recursos/{recurso_id}",
        json={
            "titulo": "Anon",
            "url": "https://example.com/x",
            "descripcion": "desc",
            "materia_id": materia.id,
        },
    )
    assert response.status_code == 401
