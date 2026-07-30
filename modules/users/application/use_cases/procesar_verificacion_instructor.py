from datetime import datetime, timezone

from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import NotFoundError
from modules.users.application.dtos import (
    ProcesarVerificacionInstructorDTO,
    SolicitudInstructorResultDTO,
)
from modules.users.domain.events import InstructorVerificationResolved
from modules.users.domain.repositories import ISolicitudInstructorRepository, IUserRepository
from modules.users.domain.value_objects import Rol, SolicitudInstructorEstado

_SOLICITUD_NO_ENCONTRADA_MSG = "Solicitud de instructor no encontrada."
_MSG_NO_ENCONTRADO = "No se encontró un investigador con ese ORCID en OpenAlex."
_MSG_NOMBRE_NO_COINCIDE = "El nombre declarado no coincide con el registrado en OpenAlex."
_MSG_SIN_PUBLICACIONES = "No se encontraron publicaciones registradas para ese ORCID."


class ProcesarVerificacionInstructorUseCase(
    BaseUseCase[ProcesarVerificacionInstructorDTO, SolicitudInstructorResultDTO]
):
    """
    Aprueba o rechaza una `SolicitudInstructor` a partir del resultado ya
    obtenido de OpenAlex (la llamada HTTP ocurre antes, en
    `infrastructure/celery_tasks.py` — este caso de uso solo decide y
    persiste). Sin bypass: basta con que falle un solo chequeo (ORCID no
    encontrado, nombre distinto, o cero publicaciones) para rechazar.
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

    def _validate(self, input_dto: ProcesarVerificacionInstructorDTO) -> None:
        solicitud = self._solicitud_repository.get_by_id(input_dto.solicitud_id)
        if solicitud is None:
            raise NotFoundError(_SOLICITUD_NO_ENCONTRADA_MSG)
        self._solicitud = solicitud

    def _execute_domain_logic(
        self, input_dto: ProcesarVerificacionInstructorDTO
    ) -> tuple[SolicitudInstructorResultDTO, list[DomainEvent]]:
        solicitud = self._solicitud

        if solicitud.estado != SolicitudInstructorEstado.PENDIENTE:
            result = SolicitudInstructorResultDTO(
                id=solicitud.id,
                estado=solicitud.estado.value,
                orcid=solicitud.orcid,
                motivo_rechazo=solicitud.motivo_rechazo,
                created_at=solicitud.created_at,
            )
            return result, []

        resultado = input_dto.resultado
        motivo_rechazo = None
        if not resultado.encontrado:
            motivo_rechazo = _MSG_NO_ENCONTRADO
        elif not resultado.coincide_nombre:
            motivo_rechazo = _MSG_NOMBRE_NO_COINCIDE
        elif resultado.works_count < 1:
            motivo_rechazo = _MSG_SIN_PUBLICACIONES

        aprobada = motivo_rechazo is None
        solicitud.estado = (
            SolicitudInstructorEstado.APROBADA if aprobada else SolicitudInstructorEstado.RECHAZADA
        )
        solicitud.motivo_rechazo = motivo_rechazo
        solicitud.resultado_verificacion = {
            "encontrado": resultado.encontrado,
            "coincide_nombre": resultado.coincide_nombre,
            "works_count": resultado.works_count,
            "nombre_openalex": resultado.nombre_openalex,
        }
        solicitud.resolved_at = datetime.now(timezone.utc)
        actualizada = self._solicitud_repository.update(solicitud)

        if aprobada:
            usuario = self._user_repository.get_by_id(solicitud.user_id)
            if usuario is not None:
                usuario.rol = Rol.INSTRUCTOR
                self._user_repository.update(usuario)

        result = SolicitudInstructorResultDTO(
            id=actualizada.id,
            estado=actualizada.estado.value,
            orcid=actualizada.orcid,
            motivo_rechazo=actualizada.motivo_rechazo,
            created_at=actualizada.created_at,
        )
        event = InstructorVerificationResolved(
            solicitud_id=actualizada.id,
            user_id=actualizada.user_id,
            aprobada=aprobada,
            motivo_rechazo=motivo_rechazo,
        )
        return result, [event]
