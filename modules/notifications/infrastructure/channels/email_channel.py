from modules.notifications.domain.entities import Notificacion
from modules.shared.infrastructure.email_client import EmailClient
from modules.users.domain.repositories import IUserRepository

_ASUNTO = "PlatLAB"


class EmailChannel:
    """
    Canal email (HE-13/UC-11). Resuelve el destinatario vía
    `IUserRepository` (id suelto, Arquitectura §8) y reusa `EmailClient`
    (Sprint 0). Si el usuario no existe (dato inconsistente) no falla —
    simplemente no envía, la notificación in-app ya quedó persistida.
    """

    def __init__(self, user_repository: IUserRepository, email_client: EmailClient | None = None):
        self._user_repository = user_repository
        self._email_client = email_client or EmailClient()

    def enviar(self, notificacion: Notificacion) -> None:
        usuario = self._user_repository.get_by_id(notificacion.user_id)
        if usuario is None:
            return
        self._email_client.send(
            to=usuario.email.value,
            subject=_ASUNTO,
            body_text=notificacion.mensaje,
        )
