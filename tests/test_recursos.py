"""
tests/test_recursos.py

Tests de integración para el filtrado de recursos en GET /recursos/.
"""

import pytest
from datetime import datetime, date


# ========== Filtrado de Recursos ==========


def test_recurso_filtrado_por_materia(client, db_session, usuario_registrado, carrera_test):
    materia = _crear_materia(db_session, carrera_test)
    user_id = usuario_registrado["response"]["id"]

    recurso = _crear_recurso(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="Recurso de Programación",
        url="https://example.com/prog.pdf",
        descripcion="Descripción del recurso",
        tipo="pdf",
        fecha_creacion=datetime(2024, 6, 15),
    )

    response = client.get(f"/recursos/?materia_id={materia.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == recurso.id
    assert data["items"][0]["materia_id"] == materia.id


def test_recurso_filtrado_por_tipo(client, db_session, usuario_registrado, carrera_test):
    materia = _crear_materia(db_session, carrera_test)
    user_id = usuario_registrado["response"]["id"]

    recurso_pdf = _crear_recurso(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="PDF",
        url="https://example.com/pdf.pdf",
        descripcion="PDF",
        tipo="pdf",
        fecha_creacion=datetime(2024, 6, 15),
    )
    _crear_recurso(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="Video",
        url="https://example.com/video.mp4",
        descripcion="Video",
        tipo="video",
        fecha_creacion=datetime(2024, 6, 15),
    )

    response = client.get("/recursos/?tipo=pdf")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == recurso_pdf.id
    assert data["items"][0]["tipo"] == "pdf"


def test_recurso_filtrado_por_rango_fechas(client, db_session, usuario_registrado, carrera_test):
    materia = _crear_materia(db_session, carrera_test)
    user_id = usuario_registrado["response"]["id"]

    recurso_en_rango = _crear_recurso(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="En rango",
        url="https://example.com/en-rango.pdf",
        descripcion="En rango",
        tipo="pdf",
        fecha_creacion=datetime(2024, 6, 15),
    )
    _crear_recurso(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="Fuera de rango",
        url="https://example.com/fuera.pdf",
        descripcion="Fuera de rango",
        tipo="pdf",
        fecha_creacion=datetime(2025, 3, 10),
    )

    response = client.get(
        "/recursos/?desde=2024-01-01&hasta=2024-12-31"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == recurso_en_rango.id


def test_recurso_filtrado_sin_resultados(client, db_session, usuario_registrado, carrera_test):
    materia = _crear_materia(db_session, carrera_test)
    user_id = usuario_registrado["response"]["id"]

    _crear_recurso(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="Recurso existente",
        url="https://example.com/existente.pdf",
        descripcion="Existe",
        tipo="pdf",
        fecha_creacion=datetime(2024, 6, 15),
    )

    response = client.get("/recursos/?materia_id=99999&tipo=audio")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_recurso_filtrado_todos_los_parametros(
    client, db_session, usuario_registrado, carrera_test
):
    materia = _crear_materia(db_session, carrera_test)
    user_id = usuario_registrado["response"]["id"]

    recurso_matching = _crear_recurso(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="Matching total",
        url="https://example.com/matching.pdf",
        descripcion="Matching",
        tipo="pdf",
        fecha_creacion=datetime(2024, 6, 15),
    )
    _crear_recurso(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="No matching",
        url="https://example.com/no-matching.pdf",
        descripcion="No matching",
        tipo="video",
        fecha_creacion=datetime(2025, 1, 1),
    )

    response = client.get(
        f"/recursos/?materia_id={materia.id}&tipo=pdf&desde=2024-01-01&hasta=2024-12-31"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == recurso_matching.id


def test_recurso_sin_filtros(client, db_session, usuario_registrado, carrera_test):
    materia = _crear_materia(db_session, carrera_test)
    user_id = usuario_registrado["response"]["id"]

    _crear_recurso(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="Recurso 1",
        url="https://example.com/1.pdf",
        descripcion="Uno",
        tipo="pdf",
        fecha_creacion=datetime(2024, 6, 15),
    )
    _crear_recurso(
        db_session,
        usuario_id=user_id,
        materia_id=materia.id,
        titulo="Recurso 2",
        url="https://example.com/2.pdf",
        descripcion="Dos",
        tipo="video",
        fecha_creacion=datetime(2024, 7, 20),
    )

    response = client.get("/recursos/")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


# ========== Helpers ==========


def _crear_materia(db_session, carrera_test):
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
    return materia


def _crear_recurso(
    db_session, usuario_id, materia_id, titulo, url, descripcion, tipo, fecha_creacion
):
    from app.features.recursos.model import Recurso

    recurso = Recurso(
        usuario_id=usuario_id,
        materia_id=materia_id,
        titulo=titulo,
        url=url,
        descripcion=descripcion,
        tipo=tipo,
        fecha_creacion=fecha_creacion,
    )
    db_session.add(recurso)
    db_session.commit()
    db_session.refresh(recurso)
    return recurso