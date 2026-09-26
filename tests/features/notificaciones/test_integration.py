"""
tests/features/notificaciones/test_integration.py

Tests de integración para flujo completo y scheduler:
- Flujo completo: subscribe → send_push_to_user → unsubscribe
- Verificar limpieza automática de suscripciones 404/410
- Test de scheduler: mock APScheduler job, verificar que llama a check_and_send_reminder_notifications_default
- Test de recordatorios próximos: crear recordatorio, ejecutar job, verificar push enviado
- Test de variables de entorno: VAPID config, window minutes, scheduler interval
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from freezegun import freeze_time

from app.features.auth.model import RolUsuario, Usuario
from app.features.materias.model import Carrera, IFTS, Materia
from app.features.notificaciones.model import PushSubscription
from app.features.notificaciones.scheduler import (
    check_and_send_reminder_notifications,
    check_and_send_reminder_notifications_default,
    get_reminder_window_minutes,
)
from app.features.notificaciones.service import PushNotificationService
from app.features.recordatorios.model import Recordatorio
from app.shared.exceptions import BadRequestError


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


def _crear_recordatorio(db_session, usuario_id: int, titulo: str, fecha: datetime, tipo: str = "parcial", materia_id: int = None) -> Recordatorio:
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


# ========== Tests: Flujo completo (subscribe → send_push_to_user → unsubscribe) ==========


@patch("app.features.notificaciones.service.webpush")
def test_flujo_completo_suscribir_enviar_desuscribir(mock_webpush, db_session, carrera_test, monkeypatch):
    """
    Test de integración: flujo completo subscribe → send_push_to_user → unsubscribe.
    Verifica que el ciclo de vida de una suscripción funciona end-to-end.
    """
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private-key")
    monkeypatch.setenv("VAPID_CLAIMS_SUB", "mailto:test@example.com")

    usuario = _crear_usuario(db_session, carrera_test.id)
    service = PushNotificationService(db_session)

    endpoint = "https://push.example.com/integration-flow"

    # 1. SUBSCRIBE: Crear suscripción
    subscribe_resp = service.subscribe(
        usuario_id=usuario.id,
        endpoint=endpoint,
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )

    assert subscribe_resp.usuario_id == usuario.id
    assert subscribe_resp.endpoint == endpoint
    assert subscribe_resp.id is not None

    # Verificar en BD
    sub_db = db_session.query(PushSubscription).filter_by(endpoint=endpoint).first()
    assert sub_db is not None
    assert sub_db.usuario_id == usuario.id

    # 2. SEND_PUSH_TO_USER: Enviar notificación
    mock_webpush.return_value = None

    send_result = service.send_push_to_user(
        usuario_id=usuario.id,
        title="Test Título",
        body="Test Cuerpo",
        data={"recordatorio_id": 123, "tipo": "parcial"},
    )

    assert send_result["sent"] == 1
    assert send_result["failed"] == 0
    assert send_result["invalid_endpoints"] == []
    mock_webpush.assert_called_once()

    # Verificar payload enviado
    call_args = mock_webpush.call_args
    import json
    payload = json.loads(call_args[1]["data"])
    assert payload["title"] == "Test Título"
    assert payload["body"] == "Test Cuerpo"
    assert payload["data"]["recordatorio_id"] == 123

    # 3. UNSUBSCRIBE: Eliminar suscripción
    unsubscribe_result = service.unsubscribe(usuario.id, endpoint)

    assert unsubscribe_result is True

    # Verificar eliminada en BD
    sub_db = db_session.query(PushSubscription).filter_by(endpoint=endpoint).first()
    assert sub_db is None

    # 4. Verificar que enviar después de desuscribir retorna 0
    mock_webpush.reset_mock()
    send_result_after = service.send_push_to_user(usuario.id, "Título", "Cuerpo")

    assert send_result_after == {"sent": 0, "failed": 0, "invalid_endpoints": []}
    mock_webpush.assert_not_called()


@patch("app.features.notificaciones.service.webpush")
def test_flujo_completo_multiples_suscripciones(mock_webpush, db_session, carrera_test, monkeypatch):
    """
    Test de integración: usuario con múltiples suscripciones.
    Verifica que send_push_to_user envía a todas y unsubscribe elimina solo la indicada.
    """
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private-key")
    monkeypatch.setenv("VAPID_CLAIMS_SUB", "mailto:test@example.com")

    usuario = _crear_usuario(db_session, carrera_test.id)
    service = PushNotificationService(db_session)

    # Crear 3 suscripciones
    endpoints = [
        "https://push.example.com/ep1",
        "https://push.example.com/ep2",
        "https://push.example.com/ep3",
    ]
    for ep in endpoints:
        service.subscribe(
            usuario_id=usuario.id,
            endpoint=ep,
            p256dh="BEl62iUYgUvw..." + "a" * 50,
            auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
        )

    mock_webpush.return_value = None

    # Enviar push - debe ir a las 3
    result = service.send_push_to_user(usuario.id, "Título", "Cuerpo")
    assert result["sent"] == 3
    assert result["failed"] == 0
    assert mock_webpush.call_count == 3

    # Eliminar solo una
    unsubscribe_result = service.unsubscribe(usuario.id, endpoints[1])
    assert unsubscribe_result is True

    # Verificar que quedan 2 en BD
    subs = db_session.query(PushSubscription).filter_by(usuario_id=usuario.id).all()
    assert len(subs) == 2
    remaining_endpoints = {s.endpoint for s in subs}
    assert remaining_endpoints == {endpoints[0], endpoints[2]}

    # Enviar push nuevamente - debe ir solo a las 2 restantes
    mock_webpush.reset_mock()
    result = service.send_push_to_user(usuario.id, "Título 2", "Cuerpo 2")
    assert result["sent"] == 2
    assert mock_webpush.call_count == 2


# ========== Tests: Limpieza automática de suscripciones 404/410 ==========


@patch("app.features.notificaciones.service.webpush")
def test_limpieza_automatica_404(mock_webpush, db_session, carrera_test, monkeypatch):
    """
    Verifica limpieza automática cuando send_push recibe 404 (Not Found).
    El endpoint inválido debe eliminarse de la BD.
    """
    from app.features.notificaciones.service import WebPushException

    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private-key")
    monkeypatch.setenv("VAPID_CLAIMS_SUB", "mailto:test@example.com")

    usuario = _crear_usuario(db_session, carrera_test.id)
    service = PushNotificationService(db_session)

    # Crear suscripción válida y una que dará 404
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/valido")
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/invalido-404")

    # Configurar mock: primera llamada OK, segunda 404
    mock_response = MagicMock()
    mock_response.status_code = 404

    def side_effect(*args, **kwargs):
        endpoint = kwargs["subscription_info"]["endpoint"]
        if "invalido-404" in endpoint:
            raise WebPushException("Not Found", response=mock_response)
        return None

    mock_webpush.side_effect = side_effect

    # Enviar push - debe limpiar automáticamente el 404
    result = service.send_push_to_user(usuario.id, "Título", "Cuerpo")

    assert result["sent"] == 1
    assert result["failed"] == 1
    assert "https://push.example.com/invalido-404" in result["invalid_endpoints"]

    # Verificar limpieza automática en BD
    assert db_session.query(PushSubscription).filter_by(endpoint="https://push.example.com/valido").first() is not None
    assert db_session.query(PushSubscription).filter_by(endpoint="https://push.example.com/invalido-404").first() is None


@patch("app.features.notificaciones.service.webpush")
def test_limpieza_automatica_410(mock_webpush, db_session, carrera_test, monkeypatch):
    """
    Verifica limpieza automática cuando send_push recibe 410 (Gone).
    El endpoint inválido debe eliminarse de la BD.
    """
    from app.features.notificaciones.service import WebPushException

    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private-key")
    monkeypatch.setenv("VAPID_CLAIMS_SUB", "mailto:test@example.com")

    usuario = _crear_usuario(db_session, carrera_test.id)
    service = PushNotificationService(db_session)

    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/valido")
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/invalido-410")

    mock_response = MagicMock()
    mock_response.status_code = 410

    def side_effect(*args, **kwargs):
        endpoint = kwargs["subscription_info"]["endpoint"]
        if "invalido-410" in endpoint:
            raise WebPushException("Gone", response=mock_response)
        return None

    mock_webpush.side_effect = side_effect

    result = service.send_push_to_user(usuario.id, "Título", "Cuerpo")

    assert result["sent"] == 1
    assert result["failed"] == 1
    assert "https://push.example.com/invalido-410" in result["invalid_endpoints"]

    # Verificar limpieza automática
    assert db_session.query(PushSubscription).filter_by(endpoint="https://push.example.com/valido").first() is not None
    assert db_session.query(PushSubscription).filter_by(endpoint="https://push.example.com/invalido-410").first() is None


@patch("app.features.notificaciones.service.webpush")
def test_limpieza_automatica_no_elimina_otros_errores(mock_webpush, db_session, carrera_test, monkeypatch):
    """
    Verifica que errores 500 NO causan limpieza automática (solo 404/410).
    """
    from app.features.notificaciones.service import WebPushException

    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private-key")
    monkeypatch.setenv("VAPID_CLAIMS_SUB", "mailto:test@example.com")

    usuario = _crear_usuario(db_session, carrera_test.id)
    service = PushNotificationService(db_session)

    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/error-500")

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_webpush.side_effect = WebPushException("Server Error", response=mock_response)

    result = service.send_push_to_user(usuario.id, "Título", "Cuerpo")

    assert result["sent"] == 0
    assert result["failed"] == 1
    assert result["invalid_endpoints"] == []  # 500 NO se considera inválido para limpieza

    # Verificar que la suscripción NO se eliminó
    assert db_session.query(PushSubscription).filter_by(endpoint="https://push.example.com/error-500").first() is not None


# ========== Tests: Scheduler - APScheduler job ==========


@patch("app.features.notificaciones.scheduler.check_and_send_reminder_notifications_default")
def test_scheduler_job_llamado_correctamente(mock_job, db_session, monkeypatch):
    """
    Test de integración del scheduler: mock APScheduler job,
    verificar que llama a check_and_send_reminder_notifications_default.
    """
    # Simular que APScheduler está disponible
    monkeypatch.setenv("PUSH_SCHEDULER_INTERVAL_MINUTES", "5")

    from app.main import lifespan, scheduler, APSCHEDULER_AVAILABLE
    from fastapi import FastAPI

    # Verificar que la función wrapper existe y es llamable
    assert check_and_send_reminder_notifications_default is not None

    # El test verifica que la función wrapper llama internamente a check_and_send_reminder_notifications
    # con SessionLocal. Hacemos un test de la función wrapper directamente.

    with patch("app.database.SessionLocal") as mock_session_factory:
        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session

        # Mock del query de recordatorios
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.all.return_value = []
        mock_session.query.return_value = mock_query

        # Llamar a la función wrapper
        stats = check_and_send_reminder_notifications_default()

        # Verificar que se llamó a SessionLocal y se cerró la sesión
        mock_session_factory.assert_called_once()
        mock_session.close.assert_called_once()

        # Verificar stats retornados
        assert stats == {
            "checked": 0,
            "sent": 0,
            "failed": 0,
            "no_subscription": 0,
            "errors": 0,
        }


def test_scheduler_interval_desde_variable_entorno(monkeypatch):
    """
    Verifica que el intervalo del scheduler se lee de PUSH_SCHEDULER_INTERVAL_MINUTES.
    """
    from app.main import _get_scheduler_interval_minutes

    # Test default
    monkeypatch.delenv("PUSH_SCHEDULER_INTERVAL_MINUTES", raising=False)
    assert _get_scheduler_interval_minutes() == 5

    # Test valor personalizado
    monkeypatch.setenv("PUSH_SCHEDULER_INTERVAL_MINUTES", "10")
    assert _get_scheduler_interval_minutes() == 10

    # Test valor inválido -> default
    monkeypatch.setenv("PUSH_SCHEDULER_INTERVAL_MINUTES", "no-es-numero")
    assert _get_scheduler_interval_minutes() == 5


def test_reminder_window_desde_variable_entorno(monkeypatch):
    """
    Verifica que la ventana de recordatorios se lee de PUSH_REMINDER_WINDOW_MINUTES.
    """
    from app.features.notificaciones.scheduler import DEFAULT_REMINDER_WINDOW_MINUTES, ENV_REMINDER_WINDOW

    # Test default
    monkeypatch.delenv(ENV_REMINDER_WINDOW, raising=False)
    assert get_reminder_window_minutes() == DEFAULT_REMINDER_WINDOW_MINUTES

    # Test valor personalizado
    monkeypatch.setenv(ENV_REMINDER_WINDOW, "30")
    assert get_reminder_window_minutes() == 30

    # Test valor inválido -> default
    monkeypatch.setenv(ENV_REMINDER_WINDOW, "no-es-numero")
    assert get_reminder_window_minutes() == DEFAULT_REMINDER_WINDOW_MINUTES


# ========== Tests: Recordatorios próximos - crear recordatorio, ejecutar job, verificar push ==========


@patch("app.features.notificaciones.service.webpush")
@freeze_time("2025-01-15 10:00:00")
def test_job_recordatorios_proximos_envia_push(mock_webpush, db_session, carrera_test, monkeypatch):
    """
    Test de integración: crear recordatorio en ventana temporal,
    ejecutar job del scheduler, verificar que se envía push.
    """
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private-key")
    monkeypatch.setenv("VAPID_CLAIMS_SUB", "mailto:test@example.com")
    monkeypatch.setenv("PUSH_REMINDER_WINDOW_MINUTES", "60")  # Ventana de 1 hora

    # Usuario con suscripción push
    usuario = _crear_usuario(db_session, carrera_test.id, email="user@test.com")
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/reminder-test")

    # Crear recordatorio DENTRO de la ventana (10:30, dentro de 30 min)
    ahora = datetime(2025, 1, 15, 10, 0, 0)
    recordatorio = _crear_recordatorio(
        db_session,
        usuario_id=usuario.id,
        titulo="Parcial de Programación",
        fecha=ahora + timedelta(minutes=30),
        tipo="parcial",
    )

    # Mock webpush
    mock_webpush.return_value = None

    # Mock SessionLocal para que use nuestra db_session de test
    with patch("app.database.SessionLocal", return_value=db_session):
        stats = check_and_send_reminder_notifications_default()

    # Verificar stats
    assert stats["checked"] == 1
    assert stats["sent"] == 1
    assert stats["failed"] == 0
    assert stats["no_subscription"] == 0
    assert stats["errors"] == 0

    # Verificar que se llamó a webpush con payload correcto
    mock_webpush.assert_called_once()
    call_args = mock_webpush.call_args
    import json
    payload = json.loads(call_args[1]["data"])
    assert payload["title"] == "Recordatorio"
    assert payload["body"] == "Parcial de Programación"
    assert payload["data"]["recordatorio_id"] == recordatorio.id
    assert payload["data"]["tipo"] == "parcial"
    assert payload["data"]["materia_id"] is None


@patch("app.features.notificaciones.service.webpush")
@freeze_time("2025-01-15 10:00:00")
def test_job_recordatorios_fuera_ventana_no_envia(mock_webpush, db_session, carrera_test, monkeypatch):
    """
    Verifica que recordatorios FUERA de la ventana temporal NO disparan push.
    """
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private-key")
    monkeypatch.setenv("VAPID_CLAIMS_SUB", "mailto:test@example.com")
    monkeypatch.setenv("PUSH_REMINDER_WINDOW_MINUTES", "15")  # Ventana de 15 min

    usuario = _crear_usuario(db_session, carrera_test.id, email="user2@test.com")
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/fuera-ventana")

    # Recordatorio FUERA de la ventana (10:30, ventana solo hasta 10:15)
    recordatorio = _crear_recordatorio(
        db_session,
        usuario_id=usuario.id,
        titulo="Recordatorio Lejano",
        fecha=datetime(2025, 1, 15, 10, 30, 0),  # 30 min en el futuro
        tipo="tp",
    )

    with patch("app.database.SessionLocal", return_value=db_session):
        stats = check_and_send_reminder_notifications_default()

    assert stats["checked"] == 0
    assert stats["sent"] == 0
    mock_webpush.assert_not_called()


@patch("app.features.notificaciones.service.webpush")
@freeze_time("2025-01-15 10:00:00")
def test_job_multiples_recordatorios_mismo_usuario(mock_webpush, db_session, carrera_test, monkeypatch):
    """
    Verifica que múltiples recordatorios para el mismo usuario
    envían múltiples notificaciones (una por recordatorio).
    """
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private-key")
    monkeypatch.setenv("VAPID_CLAIMS_SUB", "mailto:test@example.com")
    monkeypatch.setenv("PUSH_REMINDER_WINDOW_MINUTES", "60")

    usuario = _crear_usuario(db_session, carrera_test.id, email="user3@test.com")
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/multi-reminder")

    # Crear 3 recordatorios en la ventana
    ahora = datetime(2025, 1, 15, 10, 0, 0)
    for i in range(3):
        _crear_recordatorio(
            db_session,
            usuario_id=usuario.id,
            titulo=f"Recordatorio {i+1}",
            fecha=ahora + timedelta(minutes=10 * (i + 1)),
            tipo="parcial",
        )

    mock_webpush.return_value = None

    with patch("app.database.SessionLocal", return_value=db_session):
        stats = check_and_send_reminder_notifications_default()

    assert stats["checked"] == 3
    assert stats["sent"] == 3
    assert mock_webpush.call_count == 3


@patch("app.features.notificaciones.service.webpush")
@freeze_time("2025-01-15 10:00:00")
def test_job_usuario_sin_suscripcion(mock_webpush, db_session, carrera_test, monkeypatch):
    """
    Verifica que usuarios sin suscripción push se contabilizan en no_subscription.
    """
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private-key")
    monkeypatch.setenv("VAPID_CLAIMS_SUB", "mailto:test@example.com")
    monkeypatch.setenv("PUSH_REMINDER_WINDOW_MINUTES", "60")

    usuario = _crear_usuario(db_session, carrera_test.id, email="user4@test.com")
    # NO crear suscripción push

    _crear_recordatorio(
        db_session,
        usuario_id=usuario.id,
        titulo="Sin Push",
        fecha=datetime(2025, 1, 15, 10, 10, 0),
        tipo="otro",
    )

    with patch("app.database.SessionLocal", return_value=db_session):
        stats = check_and_send_reminder_notifications_default()

    assert stats["checked"] == 1
    assert stats["sent"] == 0
    assert stats["failed"] == 0
    assert stats["no_subscription"] == 1
    mock_webpush.assert_not_called()


@patch("app.features.notificaciones.service.webpush")
@freeze_time("2025-01-15 10:00:00")
def test_job_maneja_error_en_recordatorio(mock_webpush, db_session, carrera_test, monkeypatch):
    """
    Verifica que error en un recordatorio no rompe el job.
    send_push_to_user captura la excepción y la cuenta en failed.
    El job no incrementa errors porque la excepción se maneja en el service.
    """
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private-key")
    monkeypatch.setenv("VAPID_CLAIMS_SUB", "mailto:test@example.com")
    monkeypatch.setenv("PUSH_REMINDER_WINDOW_MINUTES", "60")

    usuario = _crear_usuario(db_session, carrera_test.id, email="user5@test.com")
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/error-test")

    _crear_recordatorio(
        db_session,
        usuario_id=usuario.id,
        titulo="Con Error",
        fecha=datetime(2025, 1, 15, 10, 10, 0),
        tipo="parcial",
    )

    # Simular error inesperado en webpush
    mock_webpush.side_effect = Exception("Error de red")

    with patch("app.database.SessionLocal", return_value=db_session):
        stats = check_and_send_reminder_notifications_default()

    assert stats["checked"] == 1
    assert stats["sent"] == 0
    assert stats["failed"] == 1  # send_push_to_user captura la excepción y la cuenta como failed
    assert stats["errors"] == 0  # El job no incrementa errors porque la excepción se maneja en service


# ========== Tests: Variables de entorno ==========


def test_vapid_config_desde_variables_entorno(monkeypatch):
    """
    Verifica que la configuración VAPID se lee correctamente de las variables de entorno.
    """
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "clave-publica-test")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "clave-privada-test")
    monkeypatch.setenv("VAPID_CLAIMS_SUB", "mailto:custom@test.com")

    # Crear service con db_session real para probar _load_vapid_config
    from app.database import Base, get_db
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        service = PushNotificationService(db)
        service._load_vapid_config()

        assert service._vapid_public_key == "clave-publica-test"
        assert service._vapid_private_key == "clave-privada-test"
        assert service._vapid_subject == "mailto:custom@test.com"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_vapid_config_falta_claves_lanza_error(monkeypatch, db_session):
    """
    Verifica que falta de claves VAPID lanza BadRequestError.
    """
    monkeypatch.delenv("VAPID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)

    service = PushNotificationService(db_session)

    with pytest.raises(BadRequestError) as exc_info:
        service._load_vapid_config()

    assert "VAPID" in str(exc_info.value.detail)
    assert "incompleta" in str(exc_info.value.detail)


def test_vapid_config_default_subject(monkeypatch, db_session):
    """
    Verifica que VAPID_CLAIMS_SUB tiene valor por defecto si no se define.
    """
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")
    monkeypatch.delenv("VAPID_CLAIMS_SUB", raising=False)

    service = PushNotificationService(db_session)
    service._load_vapid_config()

    assert service._vapid_subject == "mailto:admin@miifts.com"


def test_todas_variables_entorno_scheduler_y_recordatorios(monkeypatch):
    """
    Test integral: verifica todas las variables de entorno relacionadas
    con notificaciones push y scheduler.
    """
    # Variables VAPID
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "vapid-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "vapid-private")
    monkeypatch.setenv("VAPID_CLAIMS_SUB", "mailto:admin@test.com")

    # Variables scheduler
    monkeypatch.setenv("PUSH_SCHEDULER_INTERVAL_MINUTES", "10")

    # Variables recordatorios
    monkeypatch.setenv("PUSH_REMINDER_WINDOW_MINUTES", "20")

    # Verificar lectura
    from app.main import _get_scheduler_interval_minutes
    from app.features.notificaciones.scheduler import get_reminder_window_minutes

    assert _get_scheduler_interval_minutes() == 10
    assert get_reminder_window_minutes() == 20

    # Verificar service carga config
    from app.database import Base
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        service = PushNotificationService(db)
        service._load_vapid_config()

        assert service._vapid_public_key == "vapid-public"
        assert service._vapid_private_key == "vapid-private"
        assert service._vapid_subject == "mailto:admin@test.com"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ========== Tests: Endpoints REST + Service Integration ==========


@patch("app.features.notificaciones.service.webpush")
def test_integracion_endpoint_suscripcion_y_envio(mock_webpush, client, auth_headers, db_session, monkeypatch):
    """
    Test de integración API: POST /notificaciones/suscripcion → envío push → DELETE.
    """
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private-key")
    monkeypatch.setenv("VAPID_CLAIMS_SUB", "mailto:test@example.com")

    mock_webpush.return_value = None

    subscription_payload = {
        "endpoint": "https://push.example.com/integration-api",
        "p256dh": "BEl62iUYgUvw..." + "a" * 75,
        "auth": "dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==" + "b" * 10,
    }

    # 1. POST /notificaciones/suscripcion
    response = client.post(
        "/notificaciones/suscripcion",
        json=subscription_payload,
        headers=auth_headers,
    )
    assert response.status_code == 201
    sub_data = response.json()
    assert sub_data["endpoint"] == subscription_payload["endpoint"]

    # 2. Verificar envío push via service (usando la misma db_session del test)
    from app.features.notificaciones.service import PushNotificationService

    service = PushNotificationService(db_session)

    send_result = service.send_push_to_user(
        usuario_id=sub_data["usuario_id"],
        title="Test API",
        body="Cuerpo API",
        data={"recordatorio_id": 999},
    )

    assert send_result["sent"] == 1
    mock_webpush.assert_called_once()

    # 3. DELETE /notificaciones/suscripcion
    delete_payload = {"endpoint": subscription_payload["endpoint"]}
    response = client.request(
        "DELETE",
        "/notificaciones/suscripcion",
        json=delete_payload,
        headers=auth_headers,
    )
    assert response.status_code == 204

    # 4. Verificar que ya no se puede enviar (la suscripción fue eliminada)
    mock_webpush.reset_mock()
    send_result_after = service.send_push_to_user(sub_data["usuario_id"], "Test", "Test")
    assert send_result_after == {"sent": 0, "failed": 0, "invalid_endpoints": []}
    mock_webpush.assert_not_called()


# ========== Tests: Payload correcto en scheduler ==========


@patch("app.features.notificaciones.service.webpush")
@freeze_time("2025-06-20 14:00:00")
def test_scheduler_payload_incluye_campos_esperados(mock_webpush, db_session, carrera_test, monkeypatch):
    """
    Verifica que el payload del push enviado por el scheduler incluye
    todos los campos esperados: recordatorio_id, tipo, materia_id.
    """
    monkeypatch.setenv("VAPID_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("VAPID_PRIVATE_KEY", "test-private")
    monkeypatch.setenv("VAPID_CLAIMS_SUB", "mailto:test@example.com")
    monkeypatch.setenv("PUSH_REMINDER_WINDOW_MINUTES", "60")

    # Crear materia para test (usando carrera_test del fixture)
    ifts = IFTS(nombre="IFTS Test Payload", ubicacion="CABA")
    db_session.add(ifts)
    db_session.commit()
    db_session.refresh(ifts)

    carrera = Carrera(
        nombre="Carrera Test Payload",
        duracion_cuatrimestres=4,
        ifts_id=ifts.id,
    )
    db_session.add(carrera)
    db_session.commit()
    db_session.refresh(carrera)

    materia = Materia(
        nombre="Materia Test",
        codigo="MAT101",
        anio=1,
        cuatrimestre=1,
        carrera_id=carrera.id,
    )
    db_session.add(materia)
    db_session.commit()
    db_session.refresh(materia)
    materia_id = materia.id  # Guardar ID antes de que la sesión se cierre

    usuario = _crear_usuario(db_session, carrera.id, email="payload@test.com")
    _crear_suscripcion_db(db_session, usuario.id, "https://push.example.com/payload-test")

    ahora = datetime(2025, 6, 20, 14, 0, 0)
    recordatorio = _crear_recordatorio(
        db_session,
        usuario_id=usuario.id,
        titulo="Entrega TP",
        fecha=ahora + timedelta(minutes=20),
        tipo="tp",
        materia_id=materia_id,
    )
    recordatorio_id = recordatorio.id

    mock_webpush.return_value = None

    with patch("app.database.SessionLocal", return_value=db_session):
        check_and_send_reminder_notifications_default()

    mock_webpush.assert_called_once()
    call_args = mock_webpush.call_args
    import json
    payload = json.loads(call_args[1]["data"])

    assert payload["title"] == "Recordatorio"
    assert payload["body"] == "Entrega TP"
    assert payload["data"]["recordatorio_id"] == recordatorio_id
    assert payload["data"]["tipo"] == "tp"
    assert payload["data"]["materia_id"] == materia_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])