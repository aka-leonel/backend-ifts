# app/features/auth/dependencies.py

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.features.auth.service import AuthService
from app.features.auth.schema import RolUsuario, UsuarioResponse
from app.shared.exceptions import ForbiddenError

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
        raise ForbiddenError("Se requieren permisos de administrador")
    return usuario_actual


def solo_propio_o_admin(
    usuario_id: int,
    usuario_actual: UsuarioResponse = Depends(get_current_user),
) -> UsuarioResponse:
    """
    Dependencia para endpoints con `usuario_id` en el path: permite el acceso
    sólo si el usuario autenticado es el dueño de esos datos o es admin.
    Devuelve 403 en cualquier otro caso.
    """
    if usuario_actual.id != usuario_id and usuario_actual.rol != RolUsuario.ADMIN:
        raise ForbiddenError("Sólo podés acceder a tus propios datos")
    return usuario_actual