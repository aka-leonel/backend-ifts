# app/features/auth/router.py

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.features.auth.schema import UsuarioCreate, UsuarioLogin, TokenResponse, UsuarioResponse
from app.features.auth.service import AuthService
from app.features.auth.dependencies import get_current_user  # <-- importamos desde dependencies

router = APIRouter(prefix="/auth", tags=["auth"])



@router.post("/registro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UsuarioCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario."""
    service = AuthService(db)
    return service.registrar_usuario(user_data)

@router.post("/login", response_model=TokenResponse)
def login(credenciales: UsuarioLogin, db: Session = Depends(get_db)):
    """Inicia sesión y devuelve un token JWT (body JSON, lo usa el frontend)."""
    service = AuthService(db)
    return service.iniciar_sesion(credenciales)

@router.post("/token", response_model=TokenResponse)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login con formulario OAuth2 (username = email). Lo usa el botón
    'Authorize' de Swagger; el frontend sigue usando /auth/login con JSON."""
    service = AuthService(db)
    return service.iniciar_sesion(
        UsuarioLogin(email=form_data.username, password=form_data.password)
    )

@router.get("/me", response_model=UsuarioResponse)
def get_me(current_user: UsuarioResponse = Depends(get_current_user)):
    """Devuelve los datos del usuario autenticado (protegido)."""
    return current_user

@router.get("/verify", response_model=dict)
def verify_token(current_user: UsuarioResponse = Depends(get_current_user)):
    return {"valid": True, "user_id": current_user.id}