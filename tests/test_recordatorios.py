"""
tests/test_recordatorios.py

Tests de integración para el filtrado de recordatorios en GET /recordatorios/.

Todos los endpoints de recordatorios requieren JWT: la identidad sale del token
(`auth_headers` loguea al `usuario_registrado`), ya no viaja como query param.
"""

from datetime import datetime, date


# ========== Filtrado de Recordatorios ==========


def test_recordatorio_filtrado_por_tipo(
    client, db_session, usuario_registrado, auth_headers, carrera_test
):
    materia = _crear_materia(db_session, carrera_test)
    user_id = usuario_registrado["response"]["id"]

    rec1 = _crear_recordatorio(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="Examen de Programación",
        fecha=datetime(2024, 12, 15),
        tipo="examen",
    )
    _crear_recordatorio(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="TP de Programación",
        fecha=datetime(2024, 11, 20),
        tipo="tp",
    )

    response = client.get("/recordatorios/?tipo=examen", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == rec1.id
    assert data["items"][0]["tipo"] == "examen"


def test_recordatorio_filtrado_por_rango_fechas(
    client, db_session, usuario_registrado, auth_headers, carrera_test
):
    materia = _crear_materia(db_session, carrera_test)
    user_id = usuario_registrado["response"]["id"]

    rec_en_rango = _crear_recordatorio(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="En rango",
        fecha=datetime(2024, 12, 15),
        tipo="examen",
    )
    _crear_recordatorio(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="Fuera de rango",
        fecha=datetime(2025, 3, 10),
        tipo="examen",
    )

    response = client.get(
        "/recordatorios/?desde=2024-12-01&hasta=2024-12-31", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == rec_en_rango.id


def test_recordatorio_filtrado_por_materia(
    client, db_session, usuario_registrado, auth_headers, carrera_test
):
    materia1 = _crear_materia(db_session, carrera_test)
    materia2 = _crear_materia(db_session, carrera_test, codigo="MATH1", nombre="Matemática")
    user_id = usuario_registrado["response"]["id"]

    rec = _crear_recordatorio(
        db_session,
        usuario_id=user_id,
        materia_id=materia1.id,
        titulo="Examen de Programación",
        fecha=datetime(2024, 12, 15),
        tipo="examen",
    )
    _crear_recordatorio(
        db_session,
        usuario_id=user_id,
        materia_id=materia2.id,
        titulo="Examen de Matemática",
        fecha=datetime(2024, 12, 20),
        tipo="examen",
    )

    response = client.get(
        f"/recordatorios/?materia_id={materia1.id}", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == rec.id
    assert data["items"][0]["materia_id"] == materia1.id


def test_recordatorio_filtrado_sin_resultados(
    client, db_session, usuario_registrado, auth_headers, carrera_test
):
    materia = _crear_materia(db_session, carrera_test)
    user_id = usuario_registrado["response"]["id"]

    _crear_recordatorio(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="Examen existente",
        fecha=datetime(2024, 12, 15),
        tipo="examen",
    )

    response = client.get(
        "/recordatorios/?tipo=final&materia_id=99999", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_recordatorio_ordenado_por_fecha_descendente(
    client, db_session, usuario_registrado, auth_headers, carrera_test
):
    materia = _crear_materia(db_session, carrera_test)
    user_id = usuario_registrado["response"]["id"]

    rec_antiguo = _crear_recordatorio(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="Antiguo",
        fecha=datetime(2024, 10, 1),
        tipo="examen",
    )
    rec_reciente = _crear_recordatorio(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="Reciente",
        fecha=datetime(2024, 12, 15),
        tipo="examen",
    )
    rec_medio = _crear_recordatorio(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="Medio",
        fecha=datetime(2024, 11, 1),
        tipo="examen",
    )

    response = client.get("/recordatorios/?tipo=examen", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    # Deben estar ordenados por fecha.desc(): reciente, medio, antiguo
    assert data["items"][0]["id"] == rec_reciente.id
    assert data["items"][1]["id"] == rec_medio.id
    assert data["items"][2]["id"] == rec_antiguo.id


def test_recordatorio_solo_devuelve_los_del_usuario_autenticado(
    client, db_session, usuario_registrado, auth_headers, carrera_test
):
    """Un recordatorio de otro usuario no aparece en el listado propio."""
    materia = _crear_materia(db_session, carrera_test)
    user_id = usuario_registrado["response"]["id"]

    _crear_recordatorio(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="Mío",
        fecha=datetime(2024, 12, 15),
        tipo="examen",
    )
    _crear_recordatorio(
        db_session,
        usuario_id=user_id + 999,
        materia_id=materia.id,
        titulo="De otro",
        fecha=datetime(2024, 12, 16),
        tipo="examen",
    )

    response = client.get("/recordatorios/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["titulo"] == "Mío"


def test_recordatorio_sin_token(client):
    response = client.get("/recordatorios/")

    assert response.status_code == 401


# ========== Helpers ==========


def _crear_materia(db_session, carrera_test, codigo="PROG1", nombre="Programación I"):
    from app.features.materias.model import Materia

    materia = Materia(
        carrera_id=carrera_test.id,
        nombre=nombre,
        codigo=codigo,
        anio=1,
        cuatrimestre=1,
    )
    db_session.add(materia)
    db_session.commit()
    db_session.refresh(materia)
    return materia


def _crear_recordatorio(
    db_session, usuario_id, materia_id, titulo, fecha, tipo
):
    from app.features.recordatorios.model import Recordatorio

    recordatorio = Recordatorio(
        titulo=titulo,
        fecha=fecha,
        tipo=tipo,
        usuario_id=usuario_id,
        materia_id=materia_id,
    )
    db_session.add(recordatorio)
    db_session.commit()
    db_session.refresh(recordatorio)
    return recordatorio
