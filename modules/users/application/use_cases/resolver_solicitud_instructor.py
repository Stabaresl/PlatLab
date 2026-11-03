from datetime import datetime, timezone

from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from modules.users.application.dtos import (
    ResolverSolicitudInstructorDTO,
    SolicitudInstructorResultDTO,
)
from modules.users.domain.events import InstructorVerificationResolved
from modules.users.domain.repositories import ISolicitudInstructorRepository, IUserRepository
from modules.users.domain.value_objects import Rol, SolicitudInstructorEstado

_SIN_PERMISO_MSG = "Solo un administrador puede resolver solicitudes de instructor."
_NO_ENCONTRADA_MSG = "Solicitud de instructor no encontrada."
_YA_RESUELTA_MSG = "Esta solicitud ya fue resuelta."
_MOTIVO_REQUERIDO_MSG = "Indica el motivo del rechazo: el estudiante lo verá."


class ResolverSolicitudInstructorUseCase(
    BaseUseCase[ResolverSolicitudInstructorDTO, SolicitudInstructorResultDTO]
):
    """
    Un administrador aprueba o rechaza una `SolicitudInstructor` después de
    contrastar los datos declarados con el resultado de OpenAlex. Aprobar
    asciende al usuario a instructor (el rol nuevo llega a su sesión en el
    próximo refresh, ≤15 min, sin cerrar sesión). En ambos casos se notifica
    al estudiante y queda auditado con el admin como actor.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        solicitud_repository: ISolicitudInstructorRepository,
        user_repository: IUserRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._solicitud_repository = solicitud_repository
        self._user_repository = user_repository

    def _validate(self, input_dto: ResolverSolicitudInstructorDTO) -> None:
        if input_dto.actor_rol != Rol.ADMINISTRADOR.value:
            raise ForbiddenError(_SIN_PERMISO_MSG)

        solicitud = self._solicitud_repository.get_by_id(input_dto.solicitud_id)
        if solicitud is None:
            raise NotFoundError(_NO_ENCONTRADA_MSG)
        if solicitud.estado != SolicitudInstructorEstado.PENDIENTE:
            raise ConflictError(_YA_RESUELTA_MSG)
        if not input_dto.aprobar and not (input_dto.motivo or "").strip():
            raise ValidationError(_MOTIVO_REQUERIDO_MSG)

        self._solicitud = solicitud

    def _execute_domain_logic(
        self, input_dto: ResolverSolicitudInstructorDTO
    ) -> tuple[SolicitudInstructorResultDTO, list[DomainEvent]]:
        solicitud = self._solicitud
        solicitud.estado = (
            SolicitudInstructorEstado.APROBADA if input_dto.aprobar else SolicitudInstructorEstado.RECHAZADA
        )
        solicitud.motivo_rechazo = None if input_dto.aprobar else input_dto.motivo.strip()
        solicitud.resolved_at = datetime.now(timezone.utc)
        solicitud.revisada_por_id = input_dto.actor_id
        actualizada = self._solicitud_repository.update(solicitud)

        if input_dto.aprobar:
            usuario = self._user_repository.get_by_id(solicitud.user_id)
            if usuario is not None and usuario.rol == Rol.ESTUDIANTE:
                usuario.rol = Rol.INSTRUCTOR
                self._user_repository.update(usuario)

        event = InstructorVerificationResolved(
            solicitud_id=actualizada.id,
            user_id=actualizada.user_id,
            aprobada=input_dto.aprobar,
            motivo_rechazo=actualizada.motivo_rechazo,
            admin_id=input_dto.actor_id,
        )
        return (
            SolicitudInstructorResultDTO(
                id=actualizada.id,
                estado=actualizada.estado.value,
                orcid=actualizada.orcid,
                motivo_rechazo=actualizada.motivo_rechazo,
                created_at=actualizada.created_at,
            ),
            [event],
        )
