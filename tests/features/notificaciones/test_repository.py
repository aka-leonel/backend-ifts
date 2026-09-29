"""
tests/features/notificaciones/test_repository.py

Tests unitarios para PushSubscriptionRepository:
- create
- get_by_usuario
- get_by_endpoint
- get_by_usuario_and_endpoint
- delete
- delete_by_endpoint
- delete_expired_or_invalid (batch delete)
"""

from typing import List

import pytest
from sqlalchemy.exc import IntegrityError

from app.features.auth.model import Usuario, RolUsuario
from app.features.materias.model import IFTS, Carrera
from app.features.notificaciones.model import PushSubscription
from app.features.notificaciones.repository import PushSubscriptionRepository


# ========== Helpers ==========


def _crear_carrera(db_session) -> Carrera:
    ifts = IFTS(nombre="IFTS N°1", ubicacion="CABA")
    db_session.add(ifts)
    db_session.commit()
    db_session.refresh(ifts)

    carrera = Carrera(
        nombre="Tecnicatura en Programación",
        duracion_cuatrimestres=6,
        ifts_id=ifts.id,
    )
    db_session.add(carrera)
    db_session.commit()
    db_session.refresh(carrera)
    return carrera


def _crear_usuario(db_session, carrera_id: int, email: str = "test@example.com") -> Usuario:
    usuario = Usuario(
        nombre="Test",
        apellido="User",
        email=email,
        password_hash="hashed_password",
        carrera_id=carrera_id,
        rol=RolUsuario.ESTUDIANTE,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario


def _crear_repo(db_session) -> PushSubscriptionRepository:
    return PushSubscriptionRepository(db_session)


# ========== Tests: create ==========


def test_repository_create_suscripcion(db_session, carrera_test):
    """create() guarda una suscripción y la retorna con ID."""
    usuario = _crear_usuario(db_session, carrera_test.id)
    repo = _crear_repo(db_session)

    sub = repo.create(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/create-test",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )

    assert sub.id is not None
    assert sub.usuario_id == usuario.id
    assert sub.endpoint == "https://push.example.com/create-test"
    assert sub.p256dh == "BEl62iUYgUvw..." + "a" * 50
    assert sub.auth == "dGhpcyBpcyBhbiBhdXRoIHNlY3JldA=="


def test_repository_create_duplicate_usuario_endpoint_raise_integrity(db_session, carrera_test):
    """create() lanza IntegrityError si (usuario_id, endpoint) ya existe."""
    usuario = _crear_usuario(db_session, carrera_test.id)
    repo = _crear_repo(db_session)

    repo.create(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/duplicate",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )

    with pytest.raises(IntegrityError):
        repo.create(
            usuario_id=usuario.id,
            endpoint="https://push.example.com/duplicate",
            p256dh="BOtro256dhKey..." + "b" * 50,
            auth="b3Ryb0F1dGhTZWNyZXQ=",
        )


def test_repository_create_duplicate_endpoint_diferente_usuario_raise_integrity(db_session, carrera_test):
    """create() lanza IntegrityError si endpoint ya existe (unique constraint en endpoint)."""
    usuario1 = _crear_usuario(db_session, carrera_test.id, email="user1@example.com")
    usuario2 = _crear_usuario(db_session, carrera_test.id, email="user2@example.com")
    repo = _crear_repo(db_session)

    repo.create(
        usuario_id=usuario1.id,
        endpoint="https://push.example.com/shared-endpoint",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )

    with pytest.raises(IntegrityError):
        repo.create(
            usuario_id=usuario2.id,
            endpoint="https://push.example.com/shared-endpoint",
            p256dh="BOtro256dhKey..." + "b" * 50,
            auth="b3Ryb0F1dGhTZWNyZXQ=",
        )


# ========== Tests: get_by_usuario ==========


def test_repository_get_by_usuario_retorna_lista(db_session, carrera_test):
    """get_by_usuario() retorna lista de suscripciones del usuario."""
    usuario = _crear_usuario(db_session, carrera_test.id)
    repo = _crear_repo(db_session)

    repo.create(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/ep1",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )
    repo.create(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/ep2",
        p256dh="BOtro256dhKey..." + "b" * 50,
        auth="b3Ryb0F1dGhTZWNyZXQ=",
    )

    subs = repo.get_by_usuario(usuario.id)

    assert isinstance(subs, List)
    assert len(subs) == 2
    endpoints = {s.endpoint for s in subs}
    assert endpoints == {"https://push.example.com/ep1", "https://push.example.com/ep2"}


def test_repository_get_by_usuario_vacio_si_no_tiene(db_session, carrera_test):
    """get_by_usuario() retorna lista vacía si el usuario no tiene suscripciones."""
    usuario = _crear_usuario(db_session, carrera_test.id)
    repo = _crear_repo(db_session)

    subs = repo.get_by_usuario(usuario.id)

    assert subs == []


def test_repository_get_by_usuario_no_incluye_otros_usuarios(db_session, carrera_test):
    """get_by_usuario() solo retorna suscripciones del usuario indicado."""
    usuario1 = _crear_usuario(db_session, carrera_test.id, email="user1@example.com")
    usuario2 = _crear_usuario(db_session, carrera_test.id, email="user2@example.com")
    repo = _crear_repo(db_session)

    repo.create(
        usuario_id=usuario1.id,
        endpoint="https://push.example.com/user1-ep",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )
    repo.create(
        usuario_id=usuario2.id,
        endpoint="https://push.example.com/user2-ep",
        p256dh="BOtro256dhKey..." + "b" * 50,
        auth="b3Ryb0F1dGhTZWNyZXQ=",
    )

    subs = repo.get_by_usuario(usuario1.id)

    assert len(subs) == 1
    assert subs[0].endpoint == "https://push.example.com/user1-ep"


# ========== Tests: get_by_endpoint ==========


def test_repository_get_by_endpoint_encontrado(db_session, carrera_test):
    """get_by_endpoint() retorna la suscripción si existe."""
    usuario = _crear_usuario(db_session, carrera_test.id)
    repo = _crear_repo(db_session)

    repo.create(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/find-me",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )

    sub = repo.get_by_endpoint("https://push.example.com/find-me")

    assert sub is not None
    assert sub.endpoint == "https://push.example.com/find-me"
    assert sub.usuario_id == usuario.id


def test_repository_get_by_endpoint_no_encontrado_retorna_none(db_session):
    """get_by_endpoint() retorna None si no existe."""
    repo = _crear_repo(db_session)

    sub = repo.get_by_endpoint("https://push.example.com/no-existe")

    assert sub is None


# ========== Tests: get_by_usuario_and_endpoint ==========


def test_repository_get_by_usuario_and_endpoint_encontrado(db_session, carrera_test):
    """get_by_usuario_and_endpoint() retorna suscripción si coincide usuario y endpoint."""
    usuario = _crear_usuario(db_session, carrera_test.id)
    repo = _crear_repo(db_session)

    repo.create(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/both-match",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )

    sub = repo.get_by_usuario_and_endpoint(usuario.id, "https://push.example.com/both-match")

    assert sub is not None
    assert sub.usuario_id == usuario.id
    assert sub.endpoint == "https://push.example.com/both-match"


def test_repository_get_by_usuario_and_endpoint_usuario_distinto_retorna_none(db_session, carrera_test):
    """get_by_usuario_and_endpoint() retorna None si usuario no coincide."""
    usuario1 = _crear_usuario(db_session, carrera_test.id, email="user1@example.com")
    usuario2 = _crear_usuario(db_session, carrera_test.id, email="user2@example.com")
    repo = _crear_repo(db_session)

    repo.create(
        usuario_id=usuario1.id,
        endpoint="https://push.example.com/shared",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )

    sub = repo.get_by_usuario_and_endpoint(usuario2.id, "https://push.example.com/shared")

    assert sub is None


def test_repository_get_by_usuario_and_endpoint_endpoint_distinto_retorna_none(db_session, carrera_test):
    """get_by_usuario_and_endpoint() retorna None si endpoint no coincide."""
    usuario = _crear_usuario(db_session, carrera_test.id)
    repo = _crear_repo(db_session)

    repo.create(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/real-endpoint",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )

    sub = repo.get_by_usuario_and_endpoint(usuario.id, "https://push.example.com/fake-endpoint")

    assert sub is None


# ========== Tests: delete ==========


def test_repository_delete_elimina_suscripcion(db_session, carrera_test):
    """delete() elimina la suscripción y retorna True."""
    usuario = _crear_usuario(db_session, carrera_test.id)
    repo = _crear_repo(db_session)

    sub = repo.create(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/to-delete",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )

    result = repo.delete(sub)

    assert result is True
    assert db_session.query(PushSubscription).filter_by(id=sub.id).first() is None


def test_repository_delete_none_retorna_false(db_session):
    """delete(None) retorna False sin error."""
    repo = _crear_repo(db_session)

    result = repo.delete(None)

    assert result is False


# ========== Tests: delete_by_endpoint ==========


def test_repository_delete_by_endpoint_elimina_y_retorna_true(db_session, carrera_test):
    """delete_by_endpoint() elimina por endpoint y retorna True."""
    usuario = _crear_usuario(db_session, carrera_test.id)
    repo = _crear_repo(db_session)

    repo.create(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/delete-by-ep",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )

    result = repo.delete_by_endpoint("https://push.example.com/delete-by-ep")

    assert result is True
    assert repo.get_by_endpoint("https://push.example.com/delete-by-ep") is None


def test_repository_delete_by_endpoint_no_existente_retorna_false(db_session):
    """delete_by_endpoint() retorna False si no existe."""
    repo = _crear_repo(db_session)

    result = repo.delete_by_endpoint("https://push.example.com/no-existe")

    assert result is False


# ========== Tests: delete_expired_or_invalid (batch delete) ==========


def test_repository_delete_expired_or_invalid_elimina_multiples(db_session, carrera_test):
    """delete_expired_or_invalid() elimina en lote y retorna cuenta."""
    usuario = _crear_usuario(db_session, carrera_test.id)
    repo = _crear_repo(db_session)

    repo.create(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/batch1",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )
    repo.create(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/batch2",
        p256dh="BOtro256dhKey..." + "b" * 50,
        auth="b3Ryb0F1dGhTZWNyZXQ=",
    )
    repo.create(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/batch3",
        p256dh="BCuartoKey..." + "c" * 50,
        auth="Y3VhcnRvQXV0aFNlY3JldA==",
    )

    deleted = repo.delete_expired_or_invalid([
        "https://push.example.com/batch1",
        "https://push.example.com/batch3",
    ])

    assert deleted == 2
    assert repo.get_by_endpoint("https://push.example.com/batch1") is None
    assert repo.get_by_endpoint("https://push.example.com/batch2") is not None  # No eliminado
    assert repo.get_by_endpoint("https://push.example.com/batch3") is None


def test_repository_delete_expired_or_invalid_lista_vacia_retorna_cero(db_session):
    """delete_expired_or_invalid([]) retorna 0 sin error."""
    repo = _crear_repo(db_session)

    deleted = repo.delete_expired_or_invalid([])

    assert deleted == 0


def test_repository_delete_expired_or_invalid_endpoints_inexistentes_retorna_cero(db_session):
    """delete_expired_or_invalid() con endpoints inexistentes retorna 0."""
    repo = _crear_repo(db_session)

    deleted = repo.delete_expired_or_invalid([
        "https://push.example.com/no-existe-1",
        "https://push.example.com/no-existe-2",
    ])

    assert deleted == 0


def test_repository_delete_expired_or_invalid_parcial_existentes(db_session, carrera_test):
    """delete_expired_or_invalid() elimina solo los que existen."""
    usuario = _crear_usuario(db_session, carrera_test.id)
    repo = _crear_repo(db_session)

    repo.create(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/existente",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )

    deleted = repo.delete_expired_or_invalid([
        "https://push.example.com/existente",
        "https://push.example.com/no-existe",
    ])

    assert deleted == 1
    assert repo.get_by_endpoint("https://push.example.com/existente") is None


# ========== Tests: Integración múltiple ==========


def test_repository_ciclo_completo_create_get_delete(db_session, carrera_test):
    """Ciclo completo: create -> get_by_usuario -> get_by_endpoint -> delete."""
    usuario = _crear_usuario(db_session, carrera_test.id)
    repo = _crear_repo(db_session)

    # Create
    sub = repo.create(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/full-cycle",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )
    assert sub.id is not None

    # Get by usuario
    subs = repo.get_by_usuario(usuario.id)
    assert len(subs) == 1
    assert subs[0].id == sub.id

    # Get by endpoint
    found = repo.get_by_endpoint("https://push.example.com/full-cycle")
    assert found is not None
    assert found.id == sub.id

    # Get by usuario and endpoint
    found2 = repo.get_by_usuario_and_endpoint(usuario.id, "https://push.example.com/full-cycle")
    assert found2 is not None
    assert found2.id == sub.id

    # Delete
    result = repo.delete(sub)
    assert result is True

    # Verificar eliminado
    assert repo.get_by_endpoint("https://push.example.com/full-cycle") is None
    assert repo.get_by_usuario(usuario.id) == []