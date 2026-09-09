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
