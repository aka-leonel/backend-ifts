"""
tests/test_validaciones.py

Tarea "Validaciones y manejo de errores" (Integrante 5):
- validadores de schema (cuatrimestre, año, duración, notas, fecha futura)
- reglas de negocio (no borrar carrera con materias, no borrar materia con
  cursadas, materia de la carrera del alumno)
- shape consistente de error ({"detail": "..."} con la jerarquía APIException)
"""

from datetime import datetime, timedelta


# ---------- helpers ----------

def _crear_ifts_y_carrera(db_session, nombre="Otra Carrera", duracion=6):
    from app.features.materias.model import IFTS, Carrera

    ifts = IFTS(nombre="IFTS Test", ubicacion="CABA")
    db_session.add(ifts)
    db_session.commit()
    db_session.refresh(ifts)

    carrera = Carrera(nombre=nombre, duracion_cuatrimestres=duracion, ifts_id=ifts.id)
    db_session.add(carrera)
    db_session.commit()
    db_session.refresh(carrera)
    return carrera


def _payload_materia(carrera_id, **over):
    base = {
        "carrera_id": carrera_id,
        "nombre": "Programación I",
        "codigo": "PROG1",
        "anio": 1,
        "cuatrimestre": 1,
    }
    base.update(over)
    return base


# ---------- 1. validadores de schema ----------

def test_materia_cuatrimestre_invalido(client, admin_headers, carrera_test):
    r = client.post(
        "/materias/",
        json=_payload_materia(carrera_test.id, cuatrimestre=3),
        headers=admin_headers,
    )
    assert r.status_code == 422
    assert "cuatrimestre" in r.text.lower()


def test_materia_anio_invalido(client, admin_headers, carrera_test):
    r = client.post(
        "/materias/",
        json=_payload_materia(carrera_test.id, anio=0),
        headers=admin_headers,
    )
    assert r.status_code == 422


def test_materia_nombre_vacio(client, admin_headers, carrera_test):
    r = client.post(
        "/materias/",
        json=_payload_materia(carrera_test.id, nombre="   "),
        headers=admin_headers,
    )
    assert r.status_code == 422


def test_carrera_duracion_invalida(client, admin_headers, db_session):
    from app.features.materias.model import IFTS

    ifts = IFTS(nombre="IFTS N°1", ubicacion="CABA")
    db_session.add(ifts)
    db_session.commit()
    db_session.refresh(ifts)

    r = client.post(
        "/materias/carreras",
        json={"nombre": "Tec X", "duracion_cuatrimestres": 0, "ifts_id": ifts.id},
        headers=admin_headers,
    )
    assert r.status_code == 422


def test_cursada_nota_fuera_de_rango(client, auth_headers, usuario_registrado, carrera_test):
    r = client.post(
        "/materias/usuario",
        json={"materia_id": 1, "nota_final": 11},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_recordatorio_fecha_pasada(client, usuario_registrado):
    user_id = usuario_registrado["response"]["id"]
    r = client.post(
        f"/recordatorios/?usuario_id={user_id}",
        json={"titulo": "Final viejo", "fecha": "2020-01-01T10:00:00", "tipo": "final"},
    )
    assert r.status_code == 422
    assert "futura" in r.text.lower()


def test_recordatorio_fecha_futura_ok(client, usuario_registrado):
    user_id = usuario_registrado["response"]["id"]
    futura = (datetime.now() + timedelta(days=30)).replace(microsecond=0).isoformat()
    r = client.post(
        f"/recordatorios/?usuario_id={user_id}",
        json={"titulo": "Final próximo", "fecha": futura, "tipo": "final"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["titulo"] == "Final próximo"


# ---------- 2. reglas de negocio ----------

def test_no_eliminar_carrera_con_materias(client, admin_headers, carrera_test):
    creada = client.post(
        "/materias/",
        json=_payload_materia(carrera_test.id),
        headers=admin_headers,
    )
    assert creada.status_code == 201

    r = client.delete(f"/materias/carreras/{carrera_test.id}", headers=admin_headers)
    assert r.status_code == 409
    assert "materias asociadas" in r.json()["detail"].lower()


def test_eliminar_carrera_sin_materias_ok(client, admin_headers, carrera_test):
    r = client.delete(f"/materias/carreras/{carrera_test.id}", headers=admin_headers)
    assert r.status_code == 204


def test_no_eliminar_materia_con_cursadas(
    client, admin_headers, auth_headers, usuario_registrado, carrera_test
):
    materia = client.post(
        "/materias/",
        json=_payload_materia(carrera_test.id, codigo="PROG9"),
        headers=admin_headers,
    ).json()

    cursada = client.post(
        "/materias/usuario",
        json={"materia_id": materia["id"], "cursando": True},
        headers=auth_headers,
    )
    assert cursada.status_code == 201, cursada.text

    r = client.delete(f"/materias/{materia['id']}", headers=admin_headers)
    assert r.status_code == 409
    assert "cursadas" in r.json()["detail"].lower()


def test_cursar_materia_de_otra_carrera_falla(
    client, admin_headers, auth_headers, usuario_registrado, db_session
):
    otra_carrera = _crear_ifts_y_carrera(db_session, nombre="Enfermería")

    materia = client.post(
        "/materias/",
        json=_payload_materia(otra_carrera.id, codigo="ENF1"),
        headers=admin_headers,
    ).json()

    r = client.post(
        "/materias/usuario",
        json={"materia_id": materia["id"]},
        headers=auth_headers,
    )
    assert r.status_code == 409
    assert "carrera del alumno" in r.json()["detail"].lower()


def test_cursar_materia_de_mi_carrera_ok(
    client, admin_headers, auth_headers, usuario_registrado, carrera_test
):
    materia = client.post(
        "/materias/",
        json=_payload_materia(carrera_test.id, codigo="PROG2"),
        headers=admin_headers,
    ).json()

    r = client.post(
        "/materias/usuario",
        json={"materia_id": materia["id"]},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["materia_id"] == materia["id"]


# ---------- 3. shape de error unificado ----------

def test_error_404_tiene_shape_detail(client):
    r = client.get("/recursos/99999")
    assert r.status_code == 404
    body = r.json()
    assert set(body.keys()) == {"detail"}
    assert isinstance(body["detail"], str)


def test_error_422_detail_es_string_y_trae_errors(client, admin_headers, carrera_test):
    r = client.post(
        "/materias/",
        json=_payload_materia(carrera_test.id, cuatrimestre=5, codigo=""),
        headers=admin_headers,
    )
    assert r.status_code == 422
    body = r.json()
    # mismo contrato que el resto de la API: detail siempre string
    assert isinstance(body["detail"], str)
    # + desglose campo por campo para formularios
    assert isinstance(body["errors"], list)
    campos = {e["campo"] for e in body["errors"]}
    assert "cuatrimestre" in campos and "codigo" in campos
