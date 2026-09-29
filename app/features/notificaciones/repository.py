from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.features.notificaciones.model import PushSubscription


class PushSubscriptionRepository:
    """Repositorio para operaciones CRUD de suscripciones push."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        usuario_id: int,
        endpoint: str,
        p256dh: str,
        auth: str,
    ) -> PushSubscription:
        """
        Crea una nueva suscripción push.
        
        Args:
            usuario_id: ID del usuario dueño de la suscripción
            endpoint: URL del endpoint de push del navegador
            p256dh: Clave pública P-256 en base64 URL-safe
            auth: Secreto de autenticación en base64 URL-safe
            
        Returns:
            La suscripción creada
            
        Raises:
            IntegrityError: Si ya existe una suscripción con el mismo (usuario_id, endpoint)
        """
        subscription = PushSubscription(
            usuario_id=usuario_id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
        )
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def get_by_usuario(self, usuario_id: int) -> List[PushSubscription]:
        """
        Obtiene todas las suscripciones de un usuario.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Lista de suscripciones del usuario
        """
        return (
            self.db.query(PushSubscription)
            .filter(PushSubscription.usuario_id == usuario_id)
            .all()
        )

    def get_by_endpoint(self, endpoint: str) -> Optional[PushSubscription]:
        """
        Obtiene una suscripción por su endpoint.
        
        Args:
            endpoint: URL del endpoint de push
            
        Returns:
            La suscripción si existe, None en caso contrario
        """
        return (
            self.db.query(PushSubscription)
            .filter(PushSubscription.endpoint == endpoint)
            .first()
        )

    def get_by_usuario_and_endpoint(
        self, usuario_id: int, endpoint: str
    ) -> Optional[PushSubscription]:
        """
        Obtiene una suscripción por usuario y endpoint.
        
        Args:
            usuario_id: ID del usuario
            endpoint: URL del endpoint de push
            
        Returns:
            La suscripción si existe, None en caso contrario
        """
        return (
            self.db.query(PushSubscription)
            .filter(
                PushSubscription.usuario_id == usuario_id,
                PushSubscription.endpoint == endpoint,
            )
            .first()
        )

    def delete(self, subscription: PushSubscription) -> bool:
        """
        Elimina una suscripción push.
        
        Args:
            subscription: La suscripción a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        if subscription is None:
            return False
        self.db.delete(subscription)
        self.db.commit()
        return True

    def delete_by_endpoint(self, endpoint: str) -> bool:
        """
        Elimina una suscripción por su endpoint (útil para limpieza 404/410).
        
        Args:
            endpoint: URL del endpoint de push
            
        Returns:
            True si se eliminó, False si no existía
        """
        subscription = self.get_by_endpoint(endpoint)
        if subscription is None:
            return False
        self.db.delete(subscription)
        self.db.commit()
        return True

    def delete_expired_or_invalid(self, endpoints_list: List[str]) -> int:
        """
        Elimina en lote suscripciones por lista de endpoints (respuestas 404/410).
        
        Args:
            endpoints_list: Lista de endpoints a eliminar
            
        Returns:
            Número de suscripciones eliminadas
        """
        if not endpoints_list:
            return 0
        
        deleted_count = (
            self.db.query(PushSubscription)
            .filter(PushSubscription.endpoint.in_(endpoints_list))
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return deleted_count