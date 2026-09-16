import hashlib
import logging
import secrets
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
import os

from app.features.auth.repository import AuthRepository, PasswordResetRepository
from app.features.auth.schema import (
    PerfilUpdate,
    UsuarioCreate,
    UsuarioLogin,
    UsuarioResponse,
    TokenResponse,
)
from app.features.auth.model import Usuario
from app.shared.exceptions import (
    BadRequestError,
    DuplicateError,
    NotFoundError,
    UnauthorizedError,
)

_BEARER = {"WWW-Authenticate": "Bearer"}
logger = logging.getLogger(__name__)

# Mensaje único para forgot-password, exista o no el email — no revela si
# una dirección está registrada (S5-13).
FORGOT_PASSWORD_DETAIL = (
    "Si el email está registrado, vas a recibir instrucciones para "
    "restablecer tu contraseña."
)
RESET_PASSWORD_TOKEN_EXPIRE_MINUTES = 30

# Configuración de hashing (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración de JWT - estas variables deberían estar en .env
SECRET_KEY = os.getenv("SECRET_KEY", "mi-secret-key-muy-segura-cambiar-en-produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas


class AuthService:
    """
    Servicio de autenticación: maneja la lógica de registro, login y JWT.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = AuthRepository(db)
        self.reset_repository = PasswordResetRepository(db)

    # ========== Métodos de hashing ==========

    @staticmethod
    def hash_password(password: str) -> str:
        """Genera un hash bcrypt de la contraseña."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica si la contraseña en texto plano coincide con el hash."""
        return pwd_context.verify(plain_password, hashed_password)

    # ========== JWT ==========

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Genera un JWT con el payload 'sub' = user_id y otros datos.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def decode_token(self, token: str) -> dict:
        """
        Decodifica y valida un JWT. Lanza excepción si es inválido.
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            raise UnauthorizedError("Token inválido o expirado", headers=_BEARER)

    def get_user_from_token(self, token: str) -> Usuario:
        """
        Extrae el user_id del token y devuelve el objeto Usuario.
        """
        payload = self.decode_token(token)
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise UnauthorizedError("Token sin subject", headers=_BEARER)
        user_id = int(user_id_str)  # Convertir string a int
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado")
        return user

    # ========== Registro ==========

    def registrar_usuario(self, user_data: UsuarioCreate) -> UsuarioResponse:
        """
        Registra un nuevo usuario.
        Verifica que el email no exista, hashea la contraseña y guarda.
        """
        # 1. Verificar si el email ya está registrado
        existing = self.repository.get_by_email(user_data.email)
        if existing:
            raise DuplicateError("El email ya está registrado")

        # 2. Hashear la contraseña
        hashed = self.hash_password(user_data.password)

        # 3. Crear el usuario
        try:
            new_user = self.repository.create(user_data, hashed)
        except Exception:
            # Capturar errores de integridad (ej: FK a carrera que no existe)
            raise BadRequestError(
                "Error al crear usuario. Verifica que la carrera exista."
            )

        # 4. Devolver response (sin password)
        return UsuarioResponse.model_validate(new_user)

    # ========== Login ==========

    def iniciar_sesion(self, credenciales: UsuarioLogin) -> TokenResponse:
        """
        Autentica al usuario y devuelve un token JWT.
        """
        # 1. Buscar por email
        user = self.repository.get_by_email(credenciales.email)
        if not user:
            raise UnauthorizedError("Email o contraseña incorrectos", headers=_BEARER)

        # 2. Verificar contraseña
        if not self.verify_password(credenciales.password, user.password_hash):
            raise UnauthorizedError("Email o contraseña incorrectos", headers=_BEARER)

        # 3. Generar token
        access_token = self.create_access_token(data={"sub": str(user.id), "email": user.email})

        # 4. Devolver token + datos del usuario (opcional)
        user_response = UsuarioResponse.model_validate(user)
        return TokenResponse(access_token=access_token, token_type="bearer", usuario=user_response)

    # ========== Actualización de perfil ==========

    def actualizar_perfil(self, user_id: int, datos: PerfilUpdate) -> UsuarioResponse:
        """Actualiza el nombre y/o apellido del usuario autenticado (únicos campos editables).

        La carrera se muestra en el perfil pero no se cambia desde acá.
        """
        cambios = datos.model_dump(exclude_unset=True)
        if cambios:
            user = self.repository.update(user_id, **cambios)
        else:
            user = self.repository.get_by_id(user_id)

        if user is None:
            raise NotFoundError("Usuario no encontrado")
        return UsuarioResponse.model_validate(user)

    # ========== Obtener usuario actual (para dependencias) ==========

    def get_current_user(self, token: str) -> UsuarioResponse:
        """
        Obtiene el usuario autenticado a partir del token.
        Esta función se usará como dependencia en los endpoints protegidos.
        """
        user = self.get_user_from_token(token)
        return UsuarioResponse.model_validate(user)

    # ========== Olvidé mi contraseña ==========

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def solicitar_reset_password(self, email: str) -> None:
        """Genera un token de un solo uso si el email existe y lo "envía".

        La respuesta del endpoint es siempre la misma exista o no el email
        (no revelar qué direcciones están registradas), así que acá no se
        lanza ninguna excepción por email inexistente.
        """
        user = self.repository.get_by_email(email)
        if user is None:
            return

        token = secrets.token_urlsafe(32)
        expira = datetime.now(timezone.utc) + timedelta(
            minutes=RESET_PASSWORD_TOKEN_EXPIRE_MINUTES
        )
        self.reset_repository.crear(user.id, self._hash_token(token), expira)
        self._enviar_email_reset(user.email, token)

    def _enviar_email_reset(self, email: str, token: str) -> None:
        """Punto de integración con el proveedor de email.

        TODO: no hay SMTP/proveedor configurado todavía. Mientras tanto, se
        loguea el link para poder probar el flujo completo en dev.
        """
        frontend_url = os.getenv(
            "FRONTEND_RESET_PASSWORD_URL", "http://localhost:5173/reset-password"
        )
        link = f"{frontend_url}?token={token}"
        logger.info("Reset de contraseña para %s: %s", email, link)

    def restablecer_password(self, token: str, nueva_password: str) -> None:
        """Valida el token de un solo uso y actualiza la contraseña."""
        reset_token = self.reset_repository.get_valido(self._hash_token(token))
        if reset_token is None:
            raise BadRequestError("Token inválido o expirado")

        hashed = self.hash_password(nueva_password)
        self.repository.update(reset_token.usuario_id, password_hash=hashed)
        self.reset_repository.marcar_usado(reset_token.id)