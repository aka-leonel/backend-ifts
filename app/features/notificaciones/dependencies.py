# app/features/notificaciones/dependencies.py

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.features.notificaciones.service import PushNotificationService


def get_notificacion_service(db: Session = Depends(get_db)) -> PushNotificationService:
    """Dependencia que proporciona una instancia del servicio de notificaciones push."""
    return PushNotificationService(db)