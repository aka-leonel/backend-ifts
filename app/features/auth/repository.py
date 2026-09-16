from datetime import datetime, timezone

from sqlalchemy.orm import Session
from app.features.auth.model import PasswordResetToken, Usuario
from app.features.auth.schema import UsuarioCreate, RolUsuario
from typing import Optional

class AuthRepository:
    """
    Repositorio para operaciones CRUD de la tabla Usuario.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[Usuario]:
        """
        Obtiene un usuario por su ID.
        """
        return self.db.query(Usuario).filter(Usuario.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[Usuario]:
        """
        Obtiene un usuario por su email (único).
        """
        return self.db.query(Usuario).filter(Usuario.email == email).first()

    def create(self, user_data: UsuarioCreate, hashed_password: str) -> Usuario:
        """
        Crea un nuevo usuario en la base de datos.
        Recibe el schema de creación (con password en texto plano) y el hash ya calculado.

        El registro público SIEMPRE crea usuarios con rol `estudiante`. El rol
        no se toma del request para evitar escalada de privilegios; los admins
        se crean por seed o promoción manual.
        """
        db_user = Usuario(
            nombre=user_data.nombre,
            apellido=user_data.apellido,
            email=user_data.email,
            password_hash=hashed_password,
            carrera_id=user_data.carrera_id,
            rol=RolUsuario.ESTUDIANTE,
            # fecha_registro se asigna automáticamente con server_default
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)  # Para obtener el ID generado y la fecha
        return db_user

    # Métodos opcionales (pueden agregarse más adelante)
    def update(self, user_id: int, **kwargs) -> Optional[Usuario]:
        """
        Actualiza campos de un usuario (ej: cambio de email, nombre, carrera).
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user_id: int) -> bool:
        """
        Elimina un usuario (borrado físico).
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        return True


class PasswordResetRepository:
    """Repositorio para los tokens de `forgot-password` / `reset-password`."""

    def __init__(self, db: Session):
        self.db = db

    def crear(self, usuario_id: int, token_hash: str, expira: datetime) -> PasswordResetToken:
        token = PasswordResetToken(usuario_id=usuario_id, token_hash=token_hash, expira=expira)
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_valido(self, token_hash: str) -> Optional[PasswordResetToken]:
        """Devuelve el token si existe, no fue usado y no expiró. `None` si no."""
        token = (
            self.db.query(PasswordResetToken)
            .filter(PasswordResetToken.token_hash == token_hash)
            .first()
        )
        if token is None or token.usado:
            return None
        expira = token.expira
        if expira.tzinfo is None:
            expira = expira.replace(tzinfo=timezone.utc)
        if expira < datetime.now(timezone.utc):
            return None
        return token

    def marcar_usado(self, token_id: int) -> None:
        token = self.db.query(PasswordResetToken).filter(PasswordResetToken.id == token_id).first()
        if token is not None:
            token.usado = True
            self.db.commit()