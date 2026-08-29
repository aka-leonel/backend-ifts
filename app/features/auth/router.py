# app/features/auth/router.py

from fastapi import APIRouter, Depends, HTTPException, status
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
    """Inicia sesión y devuelve un token JWT."""
    service = AuthService(db)
    return service.iniciar_sesion(credenciales)

@router.get("/me", response_model=UsuarioResponse)
def get_me(current_user: UsuarioResponse = Depends(get_current_user)):
    """Devuelve los datos del usuario autenticado (protegido)."""
    return current_user

@router.get("/verify", response_model=dict)
def verify_token(current_user: UsuarioResponse = Depends(get_current_user)):
    return {"valid": True, "user_id": current_user.id}