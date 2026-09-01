from sqlalchemy.orm import Session
from app.features.auth.model import Usuario
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