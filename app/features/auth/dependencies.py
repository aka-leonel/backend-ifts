# app/features/auth/dependencies.py

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.features.auth.service import AuthService
from app.features.auth.schema import UsuarioResponse

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