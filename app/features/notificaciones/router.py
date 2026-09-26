# app/features/notificaciones/router.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.features.auth.dependencies import get_current_user
from app.features.auth.schema import UsuarioResponse
from app.features.notificaciones.dependencies import get_notificacion_service
from app.features.notificaciones.schema import (
    PushSubscriptionCreate,
    PushSubscriptionDelete,
    PushSubscriptionResponse,
)
from app.features.notificaciones.service import PushNotificationService

router = APIRouter(
    prefix="/notificaciones",
    tags=["notificaciones"],
)


@router.post(
    "/suscripcion",
    response_model=PushSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_suscripcion(
    suscripcion: PushSubscriptionCreate,
    current_user: UsuarioResponse = Depends(get_current_user),
    service: PushNotificationService = Depends(get_notificacion_service),
):
    """
    Registra o actualiza la suscripción push del usuario autenticado.

    - **endpoint**: URL del endpoint de push del navegador
    - **p256dh**: Clave pública P-256 en base64 URL-safe
    - **auth**: Secreto de autenticación en base64 URL-safe

    Retorna la suscripción creada/actualizada con su ID y fecha de creación.
    """
    return service.subscribe(
        usuario_id=current_user.id,
        endpoint=str(suscripcion.endpoint),
        p256dh=suscripcion.p256dh,
        auth=suscripcion.auth,
    )


@router.delete("/suscripcion", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_suscripcion(
    suscripcion: PushSubscriptionDelete,
    current_user: UsuarioResponse = Depends(get_current_user),
    service: PushNotificationService = Depends(get_notificacion_service),
):
    """
    Elimina la suscripción push del usuario autenticado.

    - **endpoint**: URL del endpoint de la suscripción a eliminar

    Retorna 204 No Content si se eliminó correctamente.
    Retorna 404 si la suscripción no existe para este usuario.
    """
    deleted = service.unsubscribe(
        usuario_id=current_user.id,
        endpoint=suscripcion.endpoint,
    )
    if not deleted:
        from app.shared.exceptions import NotFoundError
        raise NotFoundError("Suscripción no encontrada para este usuario")
    return None