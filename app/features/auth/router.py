from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.features.auth.schema import UsuarioCreate, UsuarioLogin, TokenResponse, UsuarioResponse
from app.features.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

# Esquema OAuth2 para obtener el token desde el header Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Dependencia para obtener el usuario actual a partir del token
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UsuarioResponse:
    service = AuthService(db)
    return service.get_current_user(token)


# ---------- ENDPOINTS ----------

@router.post("/registro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UsuarioCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario."""
    service = AuthService(db)
    return service.registrar_usuario(user_data)


@router.post("/login", response_model=TokenResponse)
def login(credenciales: UsuarioLogin, db: Session = Depends(get_db)):
    """Inicia sesión y devuelve un token JWT."""
    service = AuthService(db)
    return service.iniciar_sesion(credenciales)


@router.get("/me", response_model=UsuarioResponse)
def get_me(current_user: UsuarioResponse = Depends(get_current_user)):
    """Devuelve los datos del usuario autenticado (protegido)."""
    return current_user


# Opcional: endpoint para verificar que el token es válido (para el frontend)
@router.get("/verify", response_model=dict)
def verify_token(current_user: UsuarioResponse = Depends(get_current_user)):
    return {"valid": True, "user_id": current_user.id}