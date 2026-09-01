# app/features/auth/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.features.auth.service import AuthService
from app.features.auth.schema import RolUsuario, UsuarioResponse

# Esquema OAuth2 para extraer el token del header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UsuarioResponse:
    """
    Dependencia que obtiene el usuario autenticado a partir del token JWT.
    Puede usarse directamente en endpoints protegidos.
    """
    service = AuthService(db)
    return service.get_current_user(token)


def require_admin(
    usuario_actual: UsuarioResponse = Depends(get_current_user),
) -> UsuarioResponse:
    """
    Dependencia para operaciones sensibles: exige que el usuario autenticado
    tenga rol de administrador. Devuelve 403 si es estudiante.
    """
    if usuario_actual.rol != RolUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador",
        )
    return usuario_actual