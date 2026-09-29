"""
tests/features/notificaciones/test_service.py

Tests unitarios para PushNotificationService:
- subscribe: registrar/actualizar suscripción
- unsubscribe: eliminar suscripción
- send_push: mock pywebpush
- send_push_to_user: múltiples suscripciones
- cleanup_invalid_subscriptions: limpieza manual
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.features.auth.model import Usuario, RolUsuario
from app.features.materias.model import IFTS, Carrera
from app.features.notificaciones.model import PushSubscription
from app.features.notificaciones.schema import PushSubscriptionResponse
from app.features.notificaciones.service import PushNotificationService
from app.shared.exceptions import BadRequestError, NotFoundError


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


def _crear_suscripcion_db(db_session, usuario_id: int, endpoint: str) -> PushSubscription:
    sub = PushSubscription(
        usuario_id=usuario_id,
        endpoint=endpoint,
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)
    return sub


def _crear_service(db_session) -> PushNotificationService:
    return PushNotificationService(db_session)


# ========== Tests: Configuración VAPID ==========


def test_service_load_vapid_config_falta_claves(db_session, monkeypatch):
    """_load_vapid_config() lanza BadRequestError si faltan claves VAPID."""
    monkeypatch.delenv("VAPID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)

    service = _crear_service(db_session)

    with pytest.raises(BadRequestError) as exc_info:
        service._load_vapid_config()

    assert "VAPID" in str(exc_info.value.detail)


def test_service_load_vapid_config_falta_pywebpush(db_session, monkeypatch):
    """_load_vapid_config() lanza BadRequestError si pywebpush no está instalado."""
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    # Simular que pywebpush no está disponible
    with patch("app.features.notificaciones.service.PYWEBPUSH_AVAILABLE", False):
        service = _crear_service(db_session)

        with pytest.raises(BadRequestError) as exc_info:
            service._load_vapid_config()

        assert "pywebpush" in str(exc_info.value.detail).lower()


def test_service_load_vapid_config_exitoso(db_session, monkeypatch):
    """_load_vapid_config() carga claves correctamente."""
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private-key")
    monkeypatch.setenv("VAPID_CLAIMS_SUB", "mailto:test@example.com")

    service = _crear_service(db_session)
    service._load_vapid_config()

    assert service._vapid_public_key == "test-public-key"
    assert service._vapid_private_key == "test-private-key"
    assert service._vapid_subject == "mailto:test@example.com"


def test_service_get_vapid_claims(db_session, monkeypatch):
    """_get_vapid_claims() retorna claims con sub."""
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private-key")
    monkeypatch.setenv("VAPID_CLAIMS_SUB", "mailto:custom@example.com")

    service = _crear_service(db_session)
    service._load_vapid_config()

    claims = service._get_vapid_claims()

    assert claims == {"sub": "mailto:custom@example.com"}


# ========== Tests: subscribe ==========


def test_service_suscribe_crear_nueva(db_session, carrera_test, monkeypatch):
    """subscribe() crea nueva suscripción si no existe."""
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    usuario = _crear_usuario(db_session, carrera_test.id)
    service = _crear_service(db_session)

    response = service.subscribe(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/new-sub",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )

    assert isinstance(response, PushSubscriptionResponse)
    assert response.usuario_id == usuario.id
    assert response.endpoint == "https://push.example.com/new-sub"
    assert response.id is not None


def test_service_suscribe_actualizar_existente(db_session, carrera_test, monkeypatch):
    """subscribe() actualiza p256dh y auth si (usuario_id, endpoint) ya existe."""
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    usuario = _crear_usuario(db_session, carrera_test.id)
    service = _crear_service(db_session)

    # Primera suscripción
    service.subscribe(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/update-sub",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )

    # Segunda llamada con mismo endpoint -> actualizar
    nuevo_p256dh = "BOtro256dhKey..." + "b" * 50
    nuevo_auth = "b3Ryb0F1dGhTZWNyZXQ="
    response = service.subscribe(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/update-sub",
        p256dh=nuevo_p256dh,
        auth=nuevo_auth,
    )

    assert response.p256dh == nuevo_p256dh
    assert response.auth == nuevo_auth

    # Verificar en BD que solo hay una
    subs = db_session.query(PushSubscription).filter_by(usuario_id=usuario.id).all()
    assert len(subs) == 1


def test_service_suscribe_diferentes_endpoints_mismo_usuario(db_session, carrera_test, monkeypatch):
    """subscribe() permite múltiples endpoints para el mismo usuario."""
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    usuario = _crear_usuario(db_session, carrera_test.id)
    service = _crear_service(db_session)

    service.subscribe(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/ep1",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )
    service.subscribe(
        usuario_id=usuario.id,
        endpoint="https://push.example.com/ep2",
        p256dh="BOtro256dhKey..." + "b" * 50,
        auth="b3Ryb0F1dGhTZWNyZXQ=",
    )

    subs = db_session.query(PushSubscription).filter_by(usuario_id=usuario.id).all()
    assert len(subs) == 2


# ========== Tests: unsubscribe ==========


def test_service_unsubscribe_elimina_existente(db_session, carrera_test, monkeypatch):
    """unsubscribe() elimina suscripción existente y retorna True."""
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    usuario = _crear_usuario(db_session, carrera_test.id)
    service = _crear_service(db_session)

    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/to-unsub")

    result = service.unsubscribe(usuario.id, "https://push.example.com/to-unsub")

    assert result is True
    assert db_session.query(PushSubscription).filter_by(endpoint="https://push.example.com/to-unsub").first() is None


def test_service_unsubscribe_no_existente_retorna_false(db_session, carrera_test, monkeypatch):
    """unsubscribe() retorna False si la suscripción no existe."""
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    usuario = _crear_usuario(db_session, carrera_test.id)
    service = _crear_service(db_session)

    result = service.unsubscribe(usuario.id, "https://push.example.com/no-existe")

    assert result is False


def test_service_unsubscribe_otro_usuario_no_elimina(db_session, carrera_test, monkeypatch):
    """unsubscribe() no elimina suscripción de otro usuario."""
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    usuario1 = _crear_usuario(db_session, carrera_test.id, email="user1@example.com")
    usuario2 = _crear_usuario(db_session, carrera_test.id, email="user2@example.com")
    service = _crear_service(db_session)

    _crear_suscripcion_db(db_session, usuario1.id, "https://push.example.com/shared-ep")

    # usuario2 intenta eliminar endpoint de usuario1
    result = service.unsubscribe(usuario2.id, "https://push.example.com/shared-ep")

    assert result is False
    # Suscripción de usuario1 debe seguir existiendo
    assert db_session.query(PushSubscription).filter_by(endpoint="https://push.example.com/shared-ep").first() is not None


# ========== Tests: send_push (mock pywebpush) ==========


@patch("app.features.notificaciones.service.webpush")
def test_service_send_push_exitoso(mock_webpush, db_session, carrera_test, monkeypatch):
    """send_push() llama webpush y retorna True en éxito."""
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    usuario = _crear_usuario(db_session, carrera_test.id)
    sub = _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/send-test")
    service = _crear_service(db_session)

    mock_webpush.return_value = None  # Éxito

    result = service.send_push(sub, "Título", "Cuerpo", {"data": "extra"})

    assert result is True
    mock_webpush.assert_called_once()
    call_args = mock_webpush.call_args
    assert call_args[1]["subscription_info"]["endpoint"] == "https://push.example.com/send-test"
    assert call_args[1]["subscription_info"]["keys"]["p256dh"] == sub.p256dh
    assert call_args[1]["subscription_info"]["keys"]["auth"] == sub.auth
    assert "vapid_private_key" in call_args[1]
    assert "vapid_claims" in call_args[1]


@patch("app.features.notificaciones.service.webpush")
def test_service_send_push_payload_correcto(mock_webpush, db_session, carrera_test, monkeypatch):
    """send_push() construye payload JSON correcto."""
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    usuario = _crear_usuario(db_session, carrera_test.id)
    sub = _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/payload-test")
    service = _crear_service(db_session)

    mock_webpush.return_value = None

    service.send_push(sub, "Mi Título", "Mi Cuerpo", {"recordatorio_id": 123})

    call_args = mock_webpush.call_args
    import json
    payload = json.loads(call_args[1]["data"])
    assert payload["title"] == "Mi Título"
    assert payload["body"] == "Mi Cuerpo"
    assert payload["data"]["recordatorio_id"] == 123


@patch("app.features.notificaciones.service.webpush")
def test_service_send_push_404_retorna_false_no_lanza(mock_webpush, db_session, carrera_test, monkeypatch):
    """send_push() retorna False (no lanza) en 404/410 para limpieza automática."""
    from app.features.notificaciones.service import WebPushException

    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    usuario = _crear_usuario(db_session, carrera_test.id)
    sub = _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/404-test")
    service = _crear_service(db_session)

    # Mock response con status_code 404
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_webpush.side_effect = WebPushException("Not Found", response=mock_response)

    result = service.send_push(sub, "Título", "Cuerpo")

    assert result is False


@patch("app.features.notificaciones.service.webpush")
def test_service_send_push_410_retorna_false_no_lanza(mock_webpush, db_session, carrera_test, monkeypatch):
    """send_push() retorna False (no lanza) en 410 para limpieza automática."""
    from app.features.notificaciones.service import WebPushException

    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    usuario = _crear_usuario(db_session, carrera_test.id)
    sub = _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/410-test")
    service = _crear_service(db_session)

    mock_response = MagicMock()
    mock_response.status_code = 410
    mock_webpush.side_effect = WebPushException("Gone", response=mock_response)

    result = service.send_push(sub, "Título", "Cuerpo")

    assert result is False


@patch("app.features.notificaciones.service.webpush")
def test_service_send_push_otro_error_lanza_excepcion(mock_webpush, db_session, carrera_test, monkeypatch):
    """send_push() propaga otros errores (500, network, etc.)."""
    from app.features.notificaciones.service import WebPushException

    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    usuario = _crear_usuario(db_session, carrera_test.id)
    sub = _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/500-test")
    service = _crear_service(db_session)

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_webpush.side_effect = WebPushException("Server Error", response=mock_response)

    with pytest.raises(WebPushException):
        service.send_push(sub, "Título", "Cuerpo")


# ========== Tests: send_push_to_user ==========


@patch("app.features.notificaciones.service.webpush")
def test_service_send_push_to_user_sin_suscripciones(db_session, carrera_test, monkeypatch):
    """send_push_to_user() retorna sent=0 failed=0 si usuario no tiene suscripciones."""
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    usuario = _crear_usuario(db_session, carrera_test.id)
    service = _crear_service(db_session)

    result = service.send_push_to_user(usuario.id, "Título", "Cuerpo")

    assert result == {"sent": 0, "failed": 0, "invalid_endpoints": []}


@patch("app.features.notificaciones.service.webpush")
def test_service_send_push_to_user_una_suscripcion_exitosa(mock_webpush, db_session, carrera_test, monkeypatch):
    """send_push_to_user() envía a una suscripción y retorna sent=1."""
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    usuario = _crear_usuario(db_session, carrera_test.id)
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/user-push-1")
    service = _crear_service(db_session)

    mock_webpush.return_value = None

    result = service.send_push_to_user(usuario.id, "Título", "Cuerpo", {"tipo": "examen"})

    assert result["sent"] == 1
    assert result["failed"] == 0
    assert result["invalid_endpoints"] == []


@patch("app.features.notificaciones.service.webpush")
def test_service_send_push_to_user_multiples_suscripciones(mock_webpush, db_session, carrera_test, monkeypatch):
    """send_push_to_user() envía a múltiples suscripciones del usuario."""
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    usuario = _crear_usuario(db_session, carrera_test.id)
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/multi-1")
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/multi-2")
    service = _crear_service(db_session)

    mock_webpush.return_value = None

    result = service.send_push_to_user(usuario.id, "Título", "Cuerpo")

    assert result["sent"] == 2
    assert result["failed"] == 0
    assert mock_webpush.call_count == 2


@patch("app.features.notificaciones.service.webpush")
def test_service_send_push_to_user_mezcla_exito_fallo_404(mock_webpush, db_session, carrera_test, monkeypatch):
    """send_push_to_user() maneja mezcla de éxito y 404, limpia inválidos."""
    from app.features.notificaciones.service import WebPushException

    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    usuario = _crear_usuario(db_session, carrera_test.id)
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/valid")
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/invalid-404")
    service = _crear_service(db_session)

    # Primera llamada OK, segunda 404
    mock_response = MagicMock()
    mock_response.status_code = 404

    def side_effect(*args, **kwargs):
        endpoint = kwargs["subscription_info"]["endpoint"]
        if "invalid" in endpoint:
            raise WebPushException("Not Found", response=mock_response)
        return None

    mock_webpush.side_effect = side_effect

    result = service.send_push_to_user(usuario.id, "Título", "Cuerpo")

    assert result["sent"] == 1
    assert result["failed"] == 1
    assert "https://push.example.com/invalid-404" in result["invalid_endpoints"]

    # Verificar limpieza automática: endpoint inválido eliminado
    assert db_session.query(PushSubscription).filter_by(endpoint="https://push.example.com/invalid-404").first() is None
    assert db_session.query(PushSubscription).filter_by(endpoint="https://push.example.com/valid").first() is not None


@patch("app.features.notificaciones.service.webpush")
def test_service_send_push_to_user_error_inesperado_contabiliza_fallo(mock_webpush, db_session, carrera_test, monkeypatch):
    """send_push_to_user() contabiliza fallos inesperados sin romper el loop."""
    from app.features.notificaciones.service import WebPushException

    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")

    usuario = _crear_usuario(db_session, carrera_test.id)
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/error-500")
    service = _crear_service(db_session)

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_webpush.side_effect = WebPushException("Server Error", response=mock_response)

    result = service.send_push_to_user(usuario.id, "Título", "Cuerpo")

    assert result["sent"] == 0
    assert result["failed"] == 1
    # 500 no se considera inválido para limpieza automática
    assert result["invalid_endpoints"] == []


# ========== Tests: cleanup_invalid_subscriptions ==========


def test_service_cleanup_invalid_subscriptions_elimina_lista(db_session, carrera_test):
    """cleanup_invalid_subscriptions() elimina endpoints de la lista."""
    usuario = _crear_usuario(db_session, carrera_test.id)
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/cleanup-1")
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/cleanup-2")
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/keep")
    service = _crear_service(db_session)

    deleted = service.cleanup_invalid_subscriptions([
        "https://push.example.com/cleanup-1",
        "https://push.example.com/cleanup-2",
    ])

    assert deleted == 2
    assert db_session.query(PushSubscription).filter_by(endpoint="https://push.example.com/cleanup-1").first() is None
    assert db_session.query(PushSubscription).filter_by(endpoint="https://push.example.com/cleanup-2").first() is None
    assert db_session.query(PushSubscription).filter_by(endpoint="https://push.example.com/keep").first() is not None


def test_service_cleanup_invalid_subscriptions_lista_vacia(db_session):
    """cleanup_invalid_subscriptions([]) retorna 0."""
    service = _crear_service(db_session)

    deleted = service.cleanup_invalid_subscriptions([])

    assert deleted == 0


def test_service_cleanup_invalid_subscriptions_endpoints_inexistentes(db_session):
    """cleanup_invalid_subscriptions() con endpoints inexistentes retorna 0."""
    service = _crear_service(db_session)

    deleted = service.cleanup_invalid_subscriptions([
        "https://push.example.com/no-existe-1",
        "https://push.example.com/no-existe-2",
    ])

    assert deleted == 0