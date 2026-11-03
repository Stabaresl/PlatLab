from datetime import datetime, timezone

from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import NotFoundError
from modules.users.application.dtos import (
    RegistrarVerificacionOpenAlexDTO,
    SolicitudInstructorResultDTO,
)
from modules.users.domain.repositories import ISolicitudInstructorRepository
from modules.users.domain.value_objects import SolicitudInstructorEstado

_SOLICITUD_NO_ENCONTRADA_MSG = "Solicitud de instructor no encontrada."


class RegistrarVerificacionOpenAlexUseCase(
    BaseUseCase[RegistrarVerificacionOpenAlexDTO, SolicitudInstructorResultDTO]
):
    """
    Guarda el resultado de consultar OpenAlex en la solicitud — y nada más:
    la solicitud sigue `pendiente` hasta que un administrador la resuelva
    (`ResolverSolicitudInstructorUseCase`).

    Antes este paso aprobaba solo: bastaba con registrarse con el nombre de
    un investigador real y poner su ORCID (OpenAlex confirma que el ORCID
    existe y que el nombre coincide, no que la persona sea su dueña). Ahora
    el resultado es evidencia que el admin ve junto a los datos de quien se
    inscribió.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        solicitud_repository: ISolicitudInstructorRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._solicitud_repository = solicitud_repository

    def _validate(self, input_dto: RegistrarVerificacionOpenAlexDTO) -> None:
        solicitud = self._solicitud_repository.get_by_id(input_dto.solicitud_id)
        if solicitud is None:
            raise NotFoundError(_SOLICITUD_NO_ENCONTRADA_MSG)
        self._solicitud = solicitud

    def _execute_domain_logic(
        self, input_dto: RegistrarVerificacionOpenAlexDTO
    ) -> tuple[SolicitudInstructorResultDTO, list[DomainEvent]]:
        solicitud = self._solicitud
        # Idempotente: si un admin ya la resolvió (o la tarea se reintentó),
        # no se pisa el resultado.
        if solicitud.estado == SolicitudInstructorEstado.PENDIENTE:
            resultado = input_dto.resultado
            solicitud.resultado_verificacion = {
                "encontrado": resultado.encontrado,
                "coincide_nombre": resultado.coincide_nombre,
                "works_count": resultado.works_count,
                "nombre_openalex": resultado.nombre_openalex,
                "consultado_en": datetime.now(timezone.utc).isoformat(),
            }
            solicitud = self._solicitud_repository.update(solicitud)

        return (
            SolicitudInstructorResultDTO(
                id=solicitud.id,
                estado=solicitud.estado.value,
                orcid=solicitud.orcid,
                motivo_rechazo=solicitud.motivo_rechazo,
                created_at=solicitud.created_at,
            ),
            [],
        )
