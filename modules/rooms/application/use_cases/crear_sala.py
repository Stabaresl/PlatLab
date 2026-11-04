from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import EstadoLaboratorio, TipoLaboratorio
from modules.rooms.application.dtos import CrearSalaDTO, SalaResultDTO
from modules.rooms.application.serializacion import sala_a_dto
from modules.rooms.domain.entities import Sala
from modules.rooms.domain.events import SalaCreada
from modules.rooms.domain.repositories import ISalaRepository
from modules.rooms.domain.value_objects import generar_codigo
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import (
    BusinessRuleViolationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from modules.shared.domain.tiempo import ahora_utc
from modules.users.domain.repositories import IUserRepository

_ROLES_ANFITRION = ("instructor", "administrador")
_SIN_PERMISO_MSG = "Solo instructores y administradores pueden crear salas."
_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_LAB_SIN_SECCIONES_MSG = "El laboratorio no tiene secciones todavía."
_FECHA_PASADA_MSG = "La fecha de cierre tiene que ser en el futuro."
_SIN_CODIGO_MSG = "No se pudo generar un código de sala único. Inténtalo de nuevo."


def laboratorio_disponible_para_sala(laboratorio, actor_id, actor_rol) -> bool:
    """
    Un anfitrión abre salas sobre laboratorios publicados: cualquier
    `predeterminado`, y entre los `personalizado` solo los suyos (un admin,
    cualquiera). Es el mismo alcance que ya tiene para invitar estudiantes.
    """
    if laboratorio is None or laboratorio.estado != EstadoLaboratorio.PUBLICADO:
        return False
    if laboratorio.tipo == TipoLaboratorio.PREDETERMINADO or actor_rol == "administrador":
        return True
    return laboratorio.instructor_id == actor_id


class CrearSalaUseCase(BaseUseCase[CrearSalaDTO, SalaResultDTO]):
    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        sala_repository: ISalaRepository,
        laboratorio_repository: ILaboratorioRepository,
        user_repository: IUserRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._sala_repository = sala_repository
        self._laboratorio_repository = laboratorio_repository
        self._user_repository = user_repository

    def _validate(self, input_dto: CrearSalaDTO) -> None:
        if input_dto.actor_rol not in _ROLES_ANFITRION:
            raise ForbiddenError(_SIN_PERMISO_MSG)
        laboratorio = self._laboratorio_repository.get_by_id(input_dto.laboratorio_id)
        if not laboratorio_disponible_para_sala(laboratorio, input_dto.actor_id, input_dto.actor_rol):
            raise NotFoundError(_LAB_NO_ENCONTRADO_MSG)
        if not self._laboratorio_repository.get_secciones(laboratorio.id):
            raise BusinessRuleViolationError(_LAB_SIN_SECCIONES_MSG)
        if input_dto.fecha_fin is not None and input_dto.fecha_fin <= ahora_utc():
            raise ValidationError(_FECHA_PASADA_MSG)
        self._laboratorio = laboratorio

    def _execute_domain_logic(self, input_dto: CrearSalaDTO) -> tuple[SalaResultDTO, list[DomainEvent]]:
        codigo = next(
            (c for c in (generar_codigo() for _ in range(12)) if not self._sala_repository.existe_codigo(c)), None
        )
        if codigo is None:
            raise ConflictError(_SIN_CODIGO_MSG)

        sala = self._sala_repository.add(
            Sala(
                nombre=input_dto.nombre,
                descripcion=(input_dto.descripcion or "").strip(),
                laboratorio_id=input_dto.laboratorio_id,
                anfitrion_id=input_dto.actor_id,
                codigo=codigo,
                capacidad=input_dto.capacidad,
                fecha_fin=input_dto.fecha_fin,
            )
        )
        anfitrion = self._user_repository.get_by_id(input_dto.actor_id)
        evento = SalaCreada(sala_id=sala.id, anfitrion_id=sala.anfitrion_id, laboratorio_id=sala.laboratorio_id)
        return sala_a_dto(sala, self._laboratorio, anfitrion, participantes=0, completados=0), [evento]
