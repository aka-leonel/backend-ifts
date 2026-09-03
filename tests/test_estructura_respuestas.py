"""
tests/test_estructura_respuestas.py

Contrato de respuestas para el front:
- TODOS los listados (GET que devuelven colecciones) responden con el
  envoltorio `PaginatedResponse`: {items, total, page, per_page, total_pages}.
- Los DELETE responden 204 sin body.
- `GET /materias/correlativas/{id}` embebe la materia correlativa en `requiere`.
"""

from datetime import datetime, timedelta

PAGINADO_KEYS = {"items", "total", "page", "per_page", "total_pages"}


def _materia(db_session, carrera, codigo="PROG1", nombre="Programación I", anio=1, cuatri=1):
    from app.features.materias.model import Materia

    m = Materia(
        carrera_id=carrera.id, nombre=nombre, codigo=codigo, anio=anio, cuatrimestre=cuatri
    )
    db_session.add(m)
    db_session.commit()
    db_session.refresh(m)
    return m


# ---------- todos los listados son PaginatedResponse ----------

def test_listados_devuelven_envoltorio_paginado(
    client, db_session, carrera_test, usuario_registrado, auth_headers
):
    user_id = usuario_registrado["response"]["id"]
    _materia(db_session, carrera_test)

    rutas = [
        "/materias/carreras",
        f"/materias/carrera/{carrera_test.id}",
        "/materias/buscar?q=Prog",
        f"/materias/usuario/{user_id}",
        "/recordatorios/",
        "/recursos/",
        f"/recursos/usuario/{user_id}",
        f"/recursos/materia/1",
        "/convenios/",
        f"/convenios/carrera/{carrera_test.id}",
        "/talentotech/",
        f"/talentotech/carrera/{carrera_test.id}",
        "/talentotech/categoria/programacion",
    ]
    for ruta in rutas:
        r = client.get(ruta, headers=auth_headers)
        assert r.status_code == 200, f"{ruta} -> {r.status_code} {r.text}"
        body = r.json()
        assert set(body.keys()) == PAGINADO_KEYS, f"{ruta} devolvió {list(body.keys())}"
        assert isinstance(body["items"], list)


def test_paginacion_respeta_per_page(client, db_session):
    from app.features.materias.model import IFTS, Carrera

    ifts = IFTS(nombre="IFTS N°1", ubicacion="CABA")
    db_session.add(ifts)
    db_session.commit()
    db_session.refresh(ifts)
    for i in range(3):
        db_session.add(Carrera(nombre=f"Carrera {i}", duracion_cuatrimestres=4, ifts_id=ifts.id))
    db_session.commit()

    r = client.get("/materias/carreras?per_page=2")
    body = r.json()
    assert body["total"] == 3
    assert body["per_page"] == 2
    assert body["total_pages"] == 2
    assert len(body["items"]) == 2

    r2 = client.get("/materias/carreras?per_page=2&page=2")
    assert len(r2.json()["items"]) == 1


# ---------- correlativas con materia embebida ----------

def test_correlativas_embebe_la_materia_requerida(client, db_session, carrera_test):
    from app.features.materias.model import Correlativa

    prog1 = _materia(db_session, carrera_test, codigo="PROG1", nombre="Programación I")
    prog2 = _materia(db_session, carrera_test, codigo="PROG2", nombre="Programación II", anio=2)
    db_session.add(Correlativa(materia_id=prog2.id, requiere_id=prog1.id))
    db_session.commit()

    r = client.get(f"/materias/correlativas/{prog2.id}")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["requiere_id"] == prog1.id
    assert item["requiere"]["codigo"] == "PROG1"
    assert item["requiere"]["nombre"] == "Programación I"


# ---------- DELETE devuelve 204 sin body ----------

def test_delete_recordatorio_devuelve_204(
    client, db_session, usuario_registrado, auth_headers, carrera_test
):
    materia = _materia(db_session, carrera_test)
    futura = (datetime.now() + timedelta(days=10)).replace(microsecond=0).isoformat()
    creado = client.post(
        "/recordatorios/",
        json={"titulo": "Parcial", "fecha": futura, "tipo": "parcial", "materia_id": materia.id},
        headers=auth_headers,
    )
    rec_id = creado.json()["id"]

    r = client.delete(f"/recordatorios/{rec_id}", headers=auth_headers)
    assert r.status_code == 204
    assert r.content == b""


def test_delete_carrera_devuelve_204(client, admin_headers, carrera_test):
    r = client.delete(f"/materias/carreras/{carrera_test.id}", headers=admin_headers)
    assert r.status_code == 204
    assert r.content == b""
