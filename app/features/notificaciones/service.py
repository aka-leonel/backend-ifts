from __future__ import annotations

import json
import logging
import os
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.features.notificaciones.model import PushSubscription
from app.features.notificaciones.repository import PushSubscriptionRepository
from app.features.notificaciones.schema import PushSubscriptionResponse
from app.shared.exceptions import BadRequestError, NotFoundError

logger = logging.getLogger(__name__)

# Import condicional de pywebpush (se instala en NOTIF-008)
try:
    from pywebpush import WebPushException, webpush
    PYWEBPUSH_AVAILABLE = True
except ImportError:
    PYWEBPUSH_AVAILABLE = False
    WebPushException = Exception  # type: ignore
    webpush = None  # type: ignore


class PushNotificationService:
    """Servicio para gestión de suscripciones push y envío de notificaciones."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = PushSubscriptionRepository(db)
        self._vapid_public_key: Optional[str] = None
        self._vapid_private_key: Optional[str] = None
        self._vapid_subject: Optional[str] = None

    # ========== Configuración VAPID ==========

    def _load_vapid_config(self) -> None:
        """Carga y valida la configuración VAPID desde variables de entorno."""
        if self._vapid_public_key is not None:
            return  # Ya cargado

        self._vapid_public_key = os.getenv("VAPID_PUBLIC_KEY")
        self._vapid_private_key = os.getenv("VAPID_PRIVATE_KEY")
        self._vapid_subject = os.getenv("VAPID_CLAIMS_SUB", "mailto:admin@miifts.com")

        if not self._vapid_public_key or not self._vapid_private_key:
            raise BadRequestError(
                "Configuración VAPID incompleta. "
                "Define VAPID_PUBLIC_KEY y VAPID_PRIVATE_KEY en variables de entorno."
            )

        if not PYWEBPUSH_AVAILABLE:
            raise BadRequestError(
                "pywebpush no está instalado. Ejecuta: pip install pywebpush"
            )

    def _get_vapid_claims(self) -> dict:
        """Retorna los claims VAPID para el envío de push."""
        return {"sub": self._vapid_subject}

    # ========== Gestión de suscripciones ==========

    def subscribe(
        self, usuario_id: int, endpoint: str, p256dh: str, auth: str
    ) -> PushSubscriptionResponse:
        """
        Registra o actualiza una suscripción push para un usuario.

        Si ya existe una suscripción con el mismo (usuario_id, endpoint),
        actualiza las claves p256dh y auth.

        Args:
            usuario_id: ID del usuario
            endpoint: URL del endpoint de push del navegador
            p256dh: Clave pública P-256 en base64 URL-safe
            auth: Secreto de autenticación en base64 URL-safe

        Returns:
            La suscripción creada o actualizada
        """
        try:
            subscription = self.repository.create(
                usuario_id=usuario_id,
                endpoint=endpoint,
                p256dh=p256dh,
                auth=auth,
            )
            logger.info("Suscripción push creada para usuario %d: %s", usuario_id, endpoint)
        except IntegrityError:
            # Si falla por constraint único (usuario_id, endpoint), actualizamos
            self.db.rollback()
            existing = self.repository.get_by_usuario_and_endpoint(usuario_id, endpoint)
            if existing:
                existing.p256dh = p256dh
                existing.auth = auth
                self.db.commit()
                self.db.refresh(existing)
                subscription = existing
                logger.info(
                    "Suscripción push actualizada para usuario %d: %s", usuario_id, endpoint
                )
            else:
                # Race condition poco probable, re-lanzamos
                raise BadRequestError(
                    "Error al registrar suscripción: conflicto de integridad"
                )

        return PushSubscriptionResponse.model_validate(subscription)

    def unsubscribe(self, usuario_id: int, endpoint: str) -> bool:
        """
        Elimina la suscripción push de un usuario.

        Args:
            usuario_id: ID del usuario
            endpoint: URL del endpoint de push a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        subscription = self.repository.get_by_usuario_and_endpoint(usuario_id, endpoint)
        if subscription is None:
            return False

        self.repository.delete(subscription)
        logger.info("Suscripción push eliminada para usuario %d: %s", usuario_id, endpoint)
        return True

    # ========== Envío de notificaciones push ==========

    def send_push(
        self, subscription: PushSubscription, title: str, body: str, data: Optional[dict] = None
    ) -> bool:
        """
        Envía una notificación push a una suscripción específica.

        Args:
            subscription: La suscripción push destino
            title: Título de la notificación
            body: Cuerpo de la notificación
            data: Datos adicionales opcionales (payload customizado)

        Returns:
            True si el envío fue exitoso, False si falló con 404/410
            (otras excepciones se propagan)
        """
        self._load_vapid_config()

        payload = {
            "title": title,
            "body": body,
        }
        if data:
            payload["data"] = data

        push_data = json.dumps(payload)

        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh,
                        "auth": subscription.auth,
                    },
                },
                data=push_data,
                vapid_private_key=self._vapid_private_key,
                vapid_claims=self._get_vapid_claims(),
            )
            logger.debug("Push enviado exitosamente a %s", subscription.endpoint)
            return True

        except WebPushException as e:
            # Verificar códigos de respuesta para limpieza automática
            if e.response is not None and e.response.status_code in (404, 410):
                logger.warning(
                    "Suscripción inválida (status %d), marcando para limpieza: %s",
                    e.response.status_code,
                    subscription.endpoint,
                )
                return False
            # Otros errores se propagan para logging/manejo superior
            logger.error("Error enviando push a %s: %s", subscription.endpoint, e)
            raise

    def send_push_to_user(
        self, usuario_id: int, title: str, body: str, data: Optional[dict] = None
    ) -> dict:
        """
        Envía una notificación push a todas las suscripciones de un usuario.

        Args:
            usuario_id: ID del usuario destino
            title: Título de la notificación
            body: Cuerpo de la notificación
            data: Datos adicionales opcionales

        Returns:
            Dict con: sent (int), failed (int), invalid_endpoints (List[str])
        """
        subscriptions = self.repository.get_by_usuario(usuario_id)

        if not subscriptions:
            logger.info("Usuario %d no tiene suscripciones push activas", usuario_id)
            return {"sent": 0, "failed": 0, "invalid_endpoints": []}

        sent = 0
        failed = 0
        invalid_endpoints: list[str] = []

        for subscription in subscriptions:
            try:
                success = self.send_push(subscription, title, body, data)
                if success:
                    sent += 1
                else:
                    failed += 1
                    invalid_endpoints.append(subscription.endpoint)
            except Exception as e:
                failed += 1
                logger.error(
                    "Error inesperado enviando push a usuario %d, endpoint %s: %s",
                    usuario_id,
                    subscription.endpoint,
                    e,
                )

        # Limpieza automática de endpoints inválidos (404/410)
        if invalid_endpoints:
            deleted = self.repository.delete_expired_or_invalid(invalid_endpoints)
            logger.info(
                "Limpieza automática: %d suscripciones inválidas eliminadas para usuario %d",
                deleted,
                usuario_id,
            )

        return {
            "sent": sent,
            "failed": failed,
            "invalid_endpoints": invalid_endpoints,
        }

    def cleanup_invalid_subscriptions(self, endpoints: list[str]) -> int:
        """
        Elimina en lote suscripciones marcadas como inválidas (404/410).

        Args:
            endpoints: Lista de endpoints a eliminar

        Returns:
            Número de suscripciones eliminadas
        """
        if not endpoints:
            return 0

        deleted = self.repository.delete_expired_or_invalid(endpoints)
        logger.info("Limpieza manual: %d suscripciones eliminadas", deleted)
        return deleted