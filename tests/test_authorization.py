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


# ========== Registro público: no permite auto-asignarse rol admin ==========


def test_registro_ignora_rol_del_body(client, carrera_test):
    """Aunque el body mande rol=admin, el usuario se crea como estudiante."""
    payload = {
        "nombre": "Intruso",
        "email": "intruso@example.com",
        "password": "password123",
        "carrera_id": carrera_test.id,
        "rol": "admin",
    }
    reg = client.post("/auth/registro", json=payload)
    assert reg.status_code == 201, reg.text
    assert reg.json()["rol"] == "estudiante"

    # Y en la práctica no puede operar como admin
    login = client.post(
        "/auth/login", json={"email": payload["email"], "password": payload["password"]}
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/materias/carreras",
        json={
            "nombre": "Carrera del intruso",
            "duracion_cuatrimestres": 4,
            "ifts_id": carrera_test.ifts_id,
        },
        headers=headers,
    )
    assert resp.status_code == 403


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


# ========== Cursadas: identidad desde el token (Sprint 2 - Integrante 1) ==========
#
# `usuario_id` ya no viaja por el path en POST/PATCH/DELETE de cursadas, y en
# `GET /materias/usuario/{id}` y `GET /materias/promedio/{id}` un alumno sólo
# puede consultar lo suyo (403 si intenta lo de otro); un admin puede ver
# cualquiera.


def _id_de(client, headers) -> int:
    """Id del usuario dueño de esos headers (vía /auth/me)."""
    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200, me.text
    return me.json()["id"]


def _crear_cursada(client, headers, carrera_id, db_session, codigo="CUR1"):
    """Crea una materia en `carrera_id` y una cursada a nombre del dueño de `headers`."""
    materia = _crear_materia(db_session, carrera_id, codigo=codigo)
    resp = client.post(
        "/materias/usuario",
        json={"materia_id": materia.id, "cursando": True},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_alumno_ve_sus_cursadas(client, auth_headers, usuario_registrado):
    mi_id = usuario_registrado["response"]["id"]
    r = client.get(f"/materias/usuario/{mi_id}", headers=auth_headers)
    assert r.status_code == 200
    assert "items" in r.json()


def test_alumno_no_ve_cursadas_de_otro(
    client, auth_headers, segundo_estudiante_headers
):
    otro_id = _id_de(client, segundo_estudiante_headers)
    r = client.get(f"/materias/usuario/{otro_id}", headers=auth_headers)
    assert r.status_code == 403


def test_admin_ve_cursadas_de_cualquier_alumno(
    client, admin_headers, auth_headers, usuario_registrado
):
    alumno_id = usuario_registrado["response"]["id"]
    r = client.get(f"/materias/usuario/{alumno_id}", headers=admin_headers)
    assert r.status_code == 200


def test_ver_cursadas_sin_token(client, usuario_registrado):
    mi_id = usuario_registrado["response"]["id"]
    r = client.get(f"/materias/usuario/{mi_id}")
    assert r.status_code == 401


def test_alumno_ve_su_promedio(client, auth_headers, usuario_registrado):
    mi_id = usuario_registrado["response"]["id"]
    r = client.get(f"/materias/promedio/{mi_id}", headers=auth_headers)
    assert r.status_code == 200


def test_alumno_no_ve_promedio_de_otro(
    client, auth_headers, segundo_estudiante_headers
):
    otro_id = _id_de(client, segundo_estudiante_headers)
    r = client.get(f"/materias/promedio/{otro_id}", headers=auth_headers)
    assert r.status_code == 403


def test_alumno_agrega_cursada_a_su_propio_nombre(
    client, auth_headers, usuario_registrado, carrera_test, db_session
):
    mi_id = usuario_registrado["response"]["id"]
    cursada = _crear_cursada(client, auth_headers, carrera_test.id, db_session)
    # el dueño sale del token, no del body ni del path
    assert cursada["usuario_id"] == mi_id


def test_agregar_cursada_sin_token(client, carrera_test, db_session):
    materia = _crear_materia(db_session, carrera_test.id, codigo="ANONCUR")
    r = client.post("/materias/usuario", json={"materia_id": materia.id})
    assert r.status_code == 401


def test_alumno_no_puede_editar_cursada_de_otro(
    client, auth_headers, segundo_estudiante_headers, carrera_test, db_session
):
    # María crea su cursada
    cursada = _crear_cursada(
        client, segundo_estudiante_headers, carrera_test.id, db_session, codigo="MARIA1"
    )
    # Juan intenta modificarla: 404 (no se revela que existe)
    r = client.patch(
        f"/materias/cursada/{cursada['id']}",
        json={"nota_final": 2},
        headers=auth_headers,
    )
    assert r.status_code == 404


def test_alumno_no_puede_borrar_cursada_de_otro(
    client, auth_headers, segundo_estudiante_headers, carrera_test, db_session
):
    cursada = _crear_cursada(
        client, segundo_estudiante_headers, carrera_test.id, db_session, codigo="MARIA2"
    )
    r = client.delete(
        f"/materias/cursada/{cursada['id']}", headers=auth_headers
    )
    assert r.status_code == 404
