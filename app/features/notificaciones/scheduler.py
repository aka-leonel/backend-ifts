from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Callable

from sqlalchemy.orm import Session

from app.features.recordatorios.model import Recordatorio
from app.features.recordatorios.repository import RecordatorioRepository
from app.features.notificaciones.service import PushNotificationService

logger = logging.getLogger(__name__)

# Configuración por defecto: 15 minutos
DEFAULT_REMINDER_WINDOW_MINUTES = 15
ENV_REMINDER_WINDOW = "PUSH_REMINDER_WINDOW_MINUTES"


def get_reminder_window_minutes() -> int:
    """
    Obtiene la ventana de tiempo en minutos desde la variable de entorno.
    
    Returns:
        Ventana en minutos (default 15)
    """
    value = os.getenv(ENV_REMINDER_WINDOW, str(DEFAULT_REMINDER_WINDOW_MINUTES))
    try:
        return int(value)
    except ValueError:
        logger.warning(
            "Valor inválido para %s: '%s', usando default %d",
            ENV_REMINDER_WINDOW,
            value,
            DEFAULT_REMINDER_WINDOW_MINUTES,
        )
        return DEFAULT_REMINDER_WINDOW_MINUTES


def check_and_send_reminder_notifications(db_session_factory: Callable[[], Session]) -> dict:
    """
    Job periódico para buscar recordatorios próximos a vencer y enviar notificaciones push.
    
    Diseñado para ser llamado por APScheduler (NOTIF-007).
    
    Args:
        db_session_factory: Factory para crear sesiones de BD (ej: SessionLocal)
        
    Returns:
        Dict con estadísticas: {
            "checked": int,      # recordatorios en ventana temporal
            "sent": int,         # notificaciones enviadas exitosamente
            "failed": int,       # notificaciones fallidas
            "no_subscription": int,  # usuarios sin suscripción push
            "errors": int        # errores inesperados
        }
    """
    window_minutes = get_reminder_window_minutes()
    now = datetime.utcnow()
    window_end = now + timedelta(minutes=window_minutes)
    
    logger.info(
        "Iniciando job de recordatorios: ventana %s - %s (%d min)",
        now.isoformat(),
        window_end.isoformat(),
        window_minutes,
    )
    
    stats = {
        "checked": 0,
        "sent": 0,
        "failed": 0,
        "no_subscription": 0,
        "errors": 0,
    }
    
    # Crear sesión de BD para este job
    db: Session = db_session_factory()
    
    try:
        # Buscar recordatorios en la ventana temporal
        recordatorio_repo = RecordatorioRepository(db)
        
        # Query: recordatorios con fecha entre now y now + window
        query = (
            db.query(Recordatorio)
            .filter(Recordatorio.fecha >= now)
            .filter(Recordatorio.fecha <= window_end)
        )
        
        recordatorios = query.all()
        stats["checked"] = len(recordatorios)
        
        if not recordatorios:
            logger.debug("No hay recordatorios en la ventana temporal actual")
            return stats
        
        logger.info("Encontrados %d recordatorios en ventana temporal", len(recordatorios))
        
        # Crear service de notificaciones
        push_service = PushNotificationService(db)
        
        # Procesar cada recordatorio
        for recordatorio in recordatorios:
            try:
                usuario_id = recordatorio.usuario_id
                
                # Payload según especificación
                data_payload = {
                    "recordatorio_id": recordatorio.id,
                    "tipo": recordatorio.tipo,
                    "materia_id": recordatorio.materia_id,
                }
                
                result = push_service.send_push_to_user(
                    usuario_id=usuario_id,
                    title="Recordatorio",
                    body=recordatorio.titulo,
                    data=data_payload,
                )
                
                stats["sent"] += result["sent"]
                stats["failed"] += result["failed"]
                
                if result["sent"] == 0 and result["failed"] == 0:
                    stats["no_subscription"] += 1
                    logger.debug(
                        "Usuario %d sin suscripción push para recordatorio %d",
                        usuario_id,
                        recordatorio.id,
                    )
                elif result["sent"] > 0:
                    logger.info(
                        "Push enviado para recordatorio %d (usuario %d): %s",
                        recordatorio.id,
                        usuario_id,
                        recordatorio.titulo,
                    )
                else:
                    logger.warning(
                        "Falló envío push para recordatorio %d (usuario %d)",
                        recordatorio.id,
                        usuario_id,
                    )
                    
            except Exception as e:
                stats["errors"] += 1
                logger.error(
                    "Error procesando recordatorio %d: %s",
                    recordatorio.id,
                    e,
                    exc_info=True,
                )
        
        logger.info(
            "Job de recordatorios completado: checked=%d, sent=%d, failed=%d, "
            "no_subscription=%d, errors=%d",
            stats["checked"],
            stats["sent"],
            stats["failed"],
            stats["no_subscription"],
            stats["errors"],
        )
        
        return stats
        
    finally:
        db.close()


# Para compatibilidad con APScheduler: función wrapper que usa SessionLocal por defecto
def check_and_send_reminder_notifications_default() -> dict:
    """
    Wrapper que usa SessionLocal por defecto.
    Útil para registrar directamente en APScheduler sin factory explícita.
    """
    from app.database import SessionLocal
    return check_and_send_reminder_notifications(SessionLocal)