"""
tests/features/notificaciones/test_schema.py

Tests unitarios para schemas Pydantic de notificaciones push:
- PushSubscriptionCreate: validación entrada (endpoint URL, p256dh, auth base64)
- PushSubscriptionDelete: validación endpoint
- PushSubscriptionResponse: serialización respuesta, from_attributes=True
"""

import pytest
from pydantic import ValidationError

from app.features.notificaciones.schema import (
    PushSubscriptionCreate,
    PushSubscriptionDelete,
    PushSubscriptionResponse,
)


# ========== Tests: PushSubscriptionCreate ==========


def test_push_subscription_create_valido():
    """Schema acepta datos válidos."""
    data = {
        "endpoint": "https://push.example.com/endpoint123",
        "p256dh": "BEl62iUYgUvw..." + "a" * 75,  # 87+ chars total
        "auth": "dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==" + "b" * 10,  # 24+ chars total
    }
    schema = PushSubscriptionCreate(**data)

    assert str(schema.endpoint) == "https://push.example.com/endpoint123"
    assert schema.p256dh == data["p256dh"]
    assert schema.auth == data["auth"]


def test_push_subscription_create_endpoint_invalido_no_url():
    """Rechaza endpoint que no es URL válida."""
    data = {
        "endpoint": "no-es-una-url",
        "p256dh": "BEl62iUYgUvw..." + "a" * 75,
        "auth": "dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==" + "b" * 10,
    }
    with pytest.raises(ValidationError) as exc_info:
        PushSubscriptionCreate(**data)

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("endpoint",) for e in errors)


def test_push_subscription_create_endpoint_vacio():
    """Rechaza endpoint vacío."""
    data = {
        "endpoint": "",
        "p256dh": "BEl62iUYgUvw..." + "a" * 75,
        "auth": "dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==" + "b" * 10,
    }
    with pytest.raises(ValidationError) as exc_info:
        PushSubscriptionCreate(**data)

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("endpoint",) for e in errors)


def test_push_subscription_create_p256dh_muy_corto():
    """Rechaza p256dh menor a 88 caracteres."""
    data = {
        "endpoint": "https://push.example.com/endpoint123",
        "p256dh": "corto",  # < 87 chars
        "auth": "dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==" + "b" * 10,
    }
    with pytest.raises(ValidationError) as exc_info:
        PushSubscriptionCreate(**data)

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("p256dh",) for e in errors)


def test_push_subscription_create_p256dh_vacio():
    """Rechaza p256dh vacío o solo espacios."""
    data = {
        "endpoint": "https://push.example.com/endpoint123",
        "p256dh": "   ",
        "auth": "dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==" + "b" * 10,
    }
    with pytest.raises(ValidationError) as exc_info:
        PushSubscriptionCreate(**data)

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("p256dh",) for e in errors)


def test_push_subscription_create_auth_muy_corto():
    """Rechaza auth menor a 24 caracteres."""
    data = {
        "endpoint": "https://push.example.com/endpoint123",
        "p256dh": "BEl62iUYgUvw..." + "a" * 75,
        "auth": "corto",  # < 24 chars
    }
    with pytest.raises(ValidationError) as exc_info:
        PushSubscriptionCreate(**data)

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("auth",) for e in errors)


def test_push_subscription_create_auth_vacio():
    """Rechaza auth vacío o solo espacios."""
    data = {
        "endpoint": "https://push.example.com/endpoint123",
        "p256dh": "BEl62iUYgUvw..." + "a" * 75,
        "auth": "   ",
    }
    with pytest.raises(ValidationError) as exc_info:
        PushSubscriptionCreate(**data)

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("auth",) for e in errors)


def test_push_subscription_create_campos_requeridos():
    """Rechaza request sin campos requeridos."""
    with pytest.raises(ValidationError) as exc_info:
        PushSubscriptionCreate()

    errors = exc_info.value.errors()
    campos_faltantes = {e["loc"][0] for e in errors if e["type"] == "missing"}
    assert "endpoint" in campos_faltantes
    assert "p256dh" in campos_faltantes
    assert "auth" in campos_faltantes


def test_push_subscription_create_endpoint_strip():
    """Endpoint se hace strip de espacios."""
    data = {
        "endpoint": "  https://push.example.com/endpoint123  ",
        "p256dh": "BEl62iUYgUvw..." + "a" * 75,
        "auth": "dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==" + "b" * 10,
    }
    schema = PushSubscriptionCreate(**data)

    # HttpUrl normaliza automáticamente
    assert str(schema.endpoint) == "https://push.example.com/endpoint123"


def test_push_subscription_create_p256dh_strip():
    """p256dh se hace strip de espacios."""
    data = {
        "endpoint": "https://push.example.com/endpoint123",
        "p256dh": "  BEl62iUYgUvw..." + "a" * 75 + "  ",
        "auth": "dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==" + "b" * 10,
    }
    schema = PushSubscriptionCreate(**data)

    assert schema.p256dh == "BEl62iUYgUvw..." + "a" * 75


def test_push_subscription_create_auth_strip():
    """auth se hace strip de espacios."""
    data = {
        "endpoint": "https://push.example.com/endpoint123",
        "p256dh": "BEl62iUYgUvw..." + "a" * 75,
        "auth": "  dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==" + "b" * 10 + "  ",
    }
    schema = PushSubscriptionCreate(**data)

    assert schema.auth == "dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==" + "b" * 10


# ========== Tests: PushSubscriptionDelete ==========


def test_push_subscription_delete_valido():
    """Schema acepta endpoint válido."""
    data = {"endpoint": "https://push.example.com/endpoint123"}
    schema = PushSubscriptionDelete(**data)

    assert schema.endpoint == "https://push.example.com/endpoint123"


def test_push_subscription_delete_endpoint_vacio():
    """Rechaza endpoint vacío."""
    data = {"endpoint": ""}
    with pytest.raises(ValidationError) as exc_info:
        PushSubscriptionDelete(**data)

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("endpoint",) for e in errors)


def test_push_subscription_delete_endpoint_solo_espacios():
    """Rechaza endpoint solo espacios."""
    data = {"endpoint": "   "}
    with pytest.raises(ValidationError) as exc_info:
        PushSubscriptionDelete(**data)

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("endpoint",) for e in errors)


def test_push_subscription_delete_endpoint_strip():
    """Endpoint se hace strip."""
    data = {"endpoint": "  https://push.example.com/endpoint123  "}
    schema = PushSubscriptionDelete(**data)

    assert schema.endpoint == "https://push.example.com/endpoint123"


# ========== Tests: PushSubscriptionResponse ==========


def test_push_subscription_response_from_attributes():
    """from_attributes=True permite crear response desde modelo ORM."""
    from app.features.notificaciones.model import PushSubscription

    # Simular modelo ORM (como vendría de la BD)
    model = PushSubscription(
        id=1,
        usuario_id=42,
        endpoint="https://push.example.com/endpoint123",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
    )
    # fecha_creacion se setea por server_default, simulamos
    from datetime import datetime, timezone
    model.fecha_creacion = datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)

    response = PushSubscriptionResponse.model_validate(model)

    assert response.id == 1
    assert response.usuario_id == 42
    assert response.endpoint == "https://push.example.com/endpoint123"
    assert response.p256dh == "BEl62iUYgUvw..." + "a" * 50
    assert response.auth == "dGhpcyBpcyBhbiBhdXRoIHNlY3JldA=="
    assert response.fecha_creacion == datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)


def test_push_subscription_response_campos_completos():
    """Response incluye todos los campos esperados."""
    from app.features.notificaciones.model import PushSubscription
    from datetime import datetime, timezone

    model = PushSubscription(
        id=99,
        usuario_id=1,
        endpoint="https://push.example.com/test",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
        fecha_creacion=datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc),
    )

    response = PushSubscriptionResponse.model_validate(model)

    # Verificar todos los campos están presentes
    assert hasattr(response, "id")
    assert hasattr(response, "usuario_id")
    assert hasattr(response, "endpoint")
    assert hasattr(response, "p256dh")
    assert hasattr(response, "auth")
    assert hasattr(response, "fecha_creacion")


def test_push_subscription_response_no_expone_campos_extra():
    """Response no incluye campos no definidos en el schema."""
    from app.features.notificaciones.model import PushSubscription
    from datetime import datetime, timezone

    model = PushSubscription(
        id=1,
        usuario_id=1,
        endpoint="https://push.example.com/test",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
        fecha_creacion=datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc),
    )

    response = PushSubscriptionResponse.model_validate(model)
    dumped = response.model_dump()

    # Solo campos definidos en el schema
    assert set(dumped.keys()) == {"id", "usuario_id", "endpoint", "p256dh", "auth", "fecha_creacion"}


def test_push_subscription_response_config_from_attributes_true():
    """Verifica que model_config tiene from_attributes=True."""
    from pydantic import ConfigDict

    assert PushSubscriptionResponse.model_config.get("from_attributes") is True


# ========== Tests: Serialización JSON ==========


def test_push_subscription_create_model_dump():
    """PushSubscriptionCreate se serializa correctamente."""
    data = {
        "endpoint": "https://push.example.com/endpoint123",
        "p256dh": "BEl62iUYgUvw..." + "a" * 75,
        "auth": "dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==" + "b" * 10,
    }
    schema = PushSubscriptionCreate(**data)
    dumped = schema.model_dump()

    assert str(dumped["endpoint"]) == "https://push.example.com/endpoint123"
    assert dumped["p256dh"] == data["p256dh"]
    assert dumped["auth"] == data["auth"]


def test_push_subscription_response_model_dump():
    """PushSubscriptionResponse se serializa correctamente."""
    from app.features.notificaciones.model import PushSubscription
    from datetime import datetime, timezone

    model = PushSubscription(
        id=1,
        usuario_id=42,
        endpoint="https://push.example.com/endpoint123",
        p256dh="BEl62iUYgUvw..." + "a" * 50,
        auth="dGhpcyBpcyBhbiBhdXRoIHNlY3JldA==",
        fecha_creacion=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
    )

    response = PushSubscriptionResponse.model_validate(model)
    dumped = response.model_dump()

    assert dumped["id"] == 1
    assert dumped["usuario_id"] == 42
    assert dumped["endpoint"] == "https://push.example.com/endpoint123"
    assert isinstance(dumped["fecha_creacion"], datetime)