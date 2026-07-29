import uuid

from celery import shared_task

from modules.notifications.domain.entities import Notificacion
from modules.notifications.domain.value_objects import TipoNotificacion
from modules.notifications.infrastructure.channels.email_channel import EmailChannel
from modules.notifications.infrastructure.channels.in_app_channel import InAppChannel
from modules.notifications.infrastructure.repositories import NotificacionRepository
from modules.users.infrastructure.repositories import UserRepository


@shared_task(name="modules.notifications.infrastructure.celery_tasks.despachar_notificacion_task")
def despachar_notificacion_task(
    user_id: str,
    tipo: str,
    mensaje: str,
    entidad_tipo: str | None = None,
    entidad_id: str | None = None,
) -> None:
    """
    UC-11 paso 2: encolada por `event_listeners.py` para no bloquear el
    caso de uso que originó el evento. Persiste in-app y encola por
    separado el envío de email (E1: el reintento con backoff del email
    no debe repetir la creación in-app).
    """
    notificacion = Notificacion(
        user_id=uuid.UUID(user_id),
        tipo=TipoNotificacion(tipo),
        mensaje=mensaje,
        entidad_tipo=entidad_tipo,
        entidad_id=uuid.UUID(entidad_id) if entidad_id else None,
    )
    guardada = InAppChannel(NotificacionRepository()).enviar(notificacion)
    enviar_email_notificacion_task.delay(str(guardada.id))


@shared_task(
    name="modules.notifications.infrastructure.celery_tasks.enviar_email_notificacion_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
)
def enviar_email_notificacion_task(notificacion_id: str) -> None:
    """UC-11 E1: proveedor de email caído → reintento con backoff exponencial."""
    notificacion = NotificacionRepository().get_by_id(uuid.UUID(notificacion_id))
    if notificacion is None:
        return
    EmailChannel(UserRepository()).enviar(notificacion)
