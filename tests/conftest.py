"""
Fixtures compartidas para todos los tests.

Usa una base SQLite en memoria (independiente de miifts.db) y hace
override de la dependencia `get_db` de FastAPI para que cada test
corra en una transacción limpia, sin tocar la base real de desarrollo.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Permite correr "pytest" desde la raíz del repo sin instalar el paquete
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.features.materias.model import IFTS, Carrera  # noqa: E402

# --- Motor de base de datos de test (SQLite en memoria) ---
# StaticPool + una sola conexión: así todas las sesiones "ven" las mismas
# tablas durante todo el test, aunque sqlite:///:memory: normalmente
# crearía una DB nueva por conexión.
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Crea todas las tablas, entrega una sesión limpia y las borra al final."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """TestClient de FastAPI con la DB real reemplazada por la de test."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# --- Fixtures de datos base (IFTS / Carrera) ---
# Usuario.carrera_id y Materia.carrera_id son NOT NULL, así que casi
# todos los tests de auth y materias necesitan una carrera ya creada.


@pytest.fixture
def carrera_test(db_session) -> Carrera:
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


@pytest.fixture
def usuario_payload(carrera_test) -> dict:
    """Payload válido para POST /auth/registro."""
    return {
        "nombre": "Juan Pérez",
        "email": "juan.perez@example.com",
        "password": "password123",
        "carrera_id": carrera_test.id,
    }


@pytest.fixture
def usuario_registrado(client, usuario_payload) -> dict:
    """Registra un usuario a través de la API y devuelve su payload + response."""
    response = client.post("/auth/registro", json=usuario_payload)
    assert response.status_code == 201, response.text
    return {"payload": usuario_payload, "response": response.json()}


@pytest.fixture
def auth_headers(client, usuario_registrado) -> dict:
    """Hace login con el usuario_registrado (rol estudiante) y devuelve el header Authorization."""
    login_data = {
        "email": usuario_registrado["payload"]["email"],
        "password": usuario_registrado["payload"]["password"],
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- Fixtures de admin (para tests de autorización por rol) ---


@pytest.fixture
def admin_usuario(db_session, carrera_test) -> dict:
    """Crea un usuario con rol ADMIN directamente en la DB (sin depender del endpoint de registro)."""
    from app.features.auth.model import RolUsuario, Usuario
    from app.features.auth.service import AuthService

    password = "adminpass123"
    admin = Usuario(
        nombre="Admin Root",
        email="admin.root@example.com",
        password_hash=AuthService.hash_password(password),
        carrera_id=carrera_test.id,
        rol=RolUsuario.ADMIN,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return {"id": admin.id, "email": admin.email, "password": password}


@pytest.fixture
def admin_headers(client, admin_usuario) -> dict:
    """Hace login con el usuario admin y devuelve el header Authorization."""
    response = client.post(
        "/auth/login",
        json={"email": admin_usuario["email"], "password": admin_usuario["password"]},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
