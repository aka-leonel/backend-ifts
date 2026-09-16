# app/features/auth/router.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.features.auth.schema import (
    ForgotPasswordRequest,
    MensajeResponse,
    PerfilUpdate,
    ResetPasswordRequest,
    UsuarioCreate,
    UsuarioLogin,
    TokenResponse,
    UsuarioResponse,
    VerifyResponse,
)
from app.features.auth.service import FORGOT_PASSWORD_DETAIL, AuthService
from app.features.auth.dependencies import get_current_user  # <-- importamos desde dependencies

router = APIRouter(prefix="/auth", tags=["auth"])



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

@router.patch("/me", response_model=UsuarioResponse)
def update_me(
    cambios: PerfilUpdate,
    current_user: UsuarioResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualiza el nombre y/o apellido del usuario autenticado."""
    service = AuthService(db)
    return service.actualizar_perfil(current_user.id, cambios)

@router.get("/verify", response_model=VerifyResponse)
def verify_token(current_user: UsuarioResponse = Depends(get_current_user)):
    return VerifyResponse(valid=True, user_id=current_user.id)

@router.post("/forgot-password", response_model=MensajeResponse)
def forgot_password(datos: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Dispara el envío del email de reset. Responde siempre lo mismo,
    exista o no el email, para no revelar qué direcciones están registradas."""
    service = AuthService(db)
    service.solicitar_reset_password(datos.email)
    return MensajeResponse(detail=FORGOT_PASSWORD_DETAIL)

@router.post("/reset-password", response_model=MensajeResponse)
def reset_password(datos: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Consume el token de un solo uso y actualiza la contraseña."""
    service = AuthService(db)
    service.restablecer_password(datos.token, datos.password)
    return MensajeResponse(detail="Contraseña actualizada correctamente.")