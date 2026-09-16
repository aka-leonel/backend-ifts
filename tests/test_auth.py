"""
tests/test_auth.py

Tarea Integrante 2 - Testing y Calidad
Tests unitarios para el feature de Auth (registro, login, get_current_user).
"""


# ========== Registro ==========


def test_registro_exitoso(client, usuario_payload):
    response = client.post("/auth/registro", json=usuario_payload)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == usuario_payload["email"]
    assert data["nombre"] == usuario_payload["nombre"]
    assert data["rol"] == "estudiante"
    # El hash de la contraseña nunca debe viajar al cliente
    assert "password" not in data
    assert "password_hash" not in data


def test_registro_email_duplicado(client, usuario_registrado):
    # usuario_registrado ya registró este email una vez
    payload_repetido = usuario_registrado["payload"]

    response = client.post("/auth/registro", json=payload_repetido)

    assert response.status_code == 409
    assert "email" in response.json()["detail"].lower()


# ========== Login ==========


def test_login_exitoso(client, usuario_registrado):
    login_data = {
        "email": usuario_registrado["payload"]["email"],
        "password": usuario_registrado["payload"]["password"],
    }

    response = client.post("/auth/login", json=login_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["usuario"]["email"] == login_data["email"]


def test_login_credenciales_invalidas(client, usuario_registrado):
    email_registrado = usuario_registrado["payload"]["email"]

    # Contraseña incorrecta
    response = client.post(
        "/auth/login",
        json={"email": email_registrado, "password": "contraseña-incorrecta"},
    )
    assert response.status_code == 401

    # Email inexistente
    response = client.post(
        "/auth/login",
        json={"email": "no-existe@example.com", "password": "cualquiera123"},
    )
    assert response.status_code == 401


# ========== get_current_user ==========


def test_get_current_user_token_valido(client, auth_headers, usuario_registrado):
    response = client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == usuario_registrado["payload"]["email"]


def test_get_current_user_token_invalido(client):
    headers = {"Authorization": "Bearer token-invalido-o-truchado"}

    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 401


def test_get_current_user_sin_token(client):
    # Caso extra: ni siquiera se manda el header Authorization
    response = client.get("/auth/me")

    assert response.status_code == 401


# ========== Edición de perfil (PATCH /auth/me) ==========


def test_patch_me_actualiza_nombre(client, auth_headers):
    r = client.patch("/auth/me", json={"nombre": "Nombre Nuevo"}, headers=auth_headers)

    assert r.status_code == 200, r.text
    assert r.json()["nombre"] == "Nombre Nuevo"


def test_patch_me_sin_token_401(client):
    assert client.patch("/auth/me", json={"nombre": "X"}).status_code == 401


def test_patch_me_nombre_invalido_422(client, auth_headers):
    r = client.patch("/auth/me", json={"nombre": "A"}, headers=auth_headers)

    assert r.status_code == 422


def test_patch_me_no_cambia_carrera_email_ni_rol(client, auth_headers, usuario_registrado):
    """El contrato de `PATCH /auth/me` es `{ nombre? }`: la carrera se muestra pero
    no se edita desde el perfil, y email/rol nunca se aceptan del body."""
    carrera_original = usuario_registrado["response"]["carrera_id"]

    r = client.patch(
        "/auth/me",
        json={
            "nombre": "Otro",
            "carrera_id": carrera_original + 999,
            "email": "hacker@example.com",
            "rol": "admin",
        },
        headers=auth_headers,
    )

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["nombre"] == "Otro"
    assert data["carrera_id"] == carrera_original
    assert data["email"] == usuario_registrado["payload"]["email"]
    assert data["rol"] == "estudiante"


# ========== Olvidé mi contraseña ==========


def _pedir_token_reset(db_session, email: str) -> str:
    """Genera un token de reset igual que el endpoint, sin pasar por el email
    (que solo se loguea), y devuelve el token en texto plano para los tests."""
    import secrets
    from datetime import datetime, timedelta, timezone

    from app.features.auth.service import AuthService

    service = AuthService(db_session)
    token = secrets.token_urlsafe(32)
    user = service.repository.get_by_email(email)
    service.reset_repository.crear(
        user.id, service._hash_token(token), datetime.now(timezone.utc) + timedelta(minutes=30)
    )
    return token


def test_forgot_password_email_existente_devuelve_200(client, usuario_registrado):
    r = client.post(
        "/auth/forgot-password", json={"email": usuario_registrado["payload"]["email"]}
    )

    assert r.status_code == 200, r.text
    assert "detail" in r.json()


def test_forgot_password_email_inexistente_devuelve_mismo_200(client):
    """No debe revelar si el email está registrado: misma respuesta en ambos casos."""
    r_existe = client.post("/auth/forgot-password", json={"email": "no-existe@example.com"})

    assert r_existe.status_code == 200
    assert r_existe.json()["detail"] == (
        "Si el email está registrado, vas a recibir instrucciones para "
        "restablecer tu contraseña."
    )


def test_reset_password_exitoso(client, db_session, usuario_registrado):
    token = _pedir_token_reset(db_session, usuario_registrado["payload"]["email"])

    r = client.post(
        "/auth/reset-password", json={"token": token, "password": "nuevaClave123"}
    )
    assert r.status_code == 200, r.text

    # La contraseña vieja ya no sirve, la nueva sí
    login_vieja = client.post(
        "/auth/login",
        json={
            "email": usuario_registrado["payload"]["email"],
            "password": usuario_registrado["payload"]["password"],
        },
    )
    assert login_vieja.status_code == 401

    login_nueva = client.post(
        "/auth/login",
        json={"email": usuario_registrado["payload"]["email"], "password": "nuevaClave123"},
    )
    assert login_nueva.status_code == 200


def test_reset_password_token_usado_dos_veces_falla(client, db_session, usuario_registrado):
    token = _pedir_token_reset(db_session, usuario_registrado["payload"]["email"])

    r1 = client.post(
        "/auth/reset-password", json={"token": token, "password": "primeraClave123"}
    )
    assert r1.status_code == 200, r1.text

    r2 = client.post(
        "/auth/reset-password", json={"token": token, "password": "segundaClave123"}
    )
    assert r2.status_code == 400


def test_reset_password_token_invalido_400(client):
    r = client.post(
        "/auth/reset-password", json={"token": "token-truchado", "password": "algoValido123"}
    )
    assert r.status_code == 400


def test_reset_password_password_invalida_422(client, db_session, usuario_registrado):
    token = _pedir_token_reset(db_session, usuario_registrado["payload"]["email"])

    r = client.post("/auth/reset-password", json={"token": token, "password": "corta1"})
    assert r.status_code == 422
