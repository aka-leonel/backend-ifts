from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os

from app.features.auth.repository import AuthRepository
from app.features.auth.schema import UsuarioCreate, UsuarioLogin, UsuarioResponse, TokenResponse
from app.features.auth.model import Usuario

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
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def get_user_from_token(self, token: str) -> Usuario:
        """
        Extrae el user_id del token y devuelve el objeto Usuario.
        """
        payload = self.decode_token(token)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sin subject")
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
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
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email ya está registrado"
            )

        # 2. Hashear la contraseña
        hashed = self.hash_password(user_data.password)

        # 3. Crear el usuario
        try:
            new_user = self.repository.create(user_data, hashed)
        except Exception as e:
            # Capturar errores de integridad (ej: FK a carrera que no existe)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al crear usuario. Verifica que la carrera exista."
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 2. Verificar contraseña
        if not self.verify_password(credenciales.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. Generar token
        access_token = self.create_access_token(data={"sub": user.id, "email": user.email})

        # 4. Devolver token + datos del usuario (opcional)
        user_response = UsuarioResponse.model_validate(user)
        return TokenResponse(access_token=access_token, token_type="bearer", usuario=user_response)

    # ========== Obtener usuario actual (para dependencias) ==========

    def get_current_user(self, token: str) -> UsuarioResponse:
        """
        Obtiene el usuario autenticado a partir del token.
        Esta función se usará como dependencia en los endpoints protegidos.
        """
        user = self.get_user_from_token(token)
        return UsuarioResponse.model_validate(user)