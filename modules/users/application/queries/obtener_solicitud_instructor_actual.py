import uuid

from modules.users.application.dtos import SolicitudInstructorResultDTO
from modules.users.domain.repositories import ISolicitudInstructorRepository


class ObtenerSolicitudInstructorActualQuery:
    """
    `GET /users/instructor-requests/mine/` — la última solicitud del
    usuario autenticado (pendiente/aprobada/rechazada), para que el
    frontend muestre el estado en vez del formulario ya enviado.
    """

    def __init__(self, solicitud_repository: ISolicitudInstructorRepository):
        self._repo = solicitud_repository

    def execute(self, actor_id: uuid.UUID) -> SolicitudInstructorResultDTO | None:
        solicitud = self._repo.get_ultima_by_user_id(actor_id)
        if solicitud is None:
            return None

        return SolicitudInstructorResultDTO(
            id=solicitud.id,
            estado=solicitud.estado.value,
            orcid=solicitud.orcid,
            motivo_rechazo=solicitud.motivo_rechazo,
            created_at=solicitud.created_at,
        )
