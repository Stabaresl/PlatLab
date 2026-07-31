from modules.gamification.application.dtos import AvatarResultDTO, SubirAvatarDTO
from modules.gamification.domain.entities import PerfilJugador
from modules.gamification.domain.repositories import IPerfilJugadorRepository
from modules.gamification.domain.value_objects import AvatarTipo
from modules.gamification.infrastructure.avatar_storage import guardar_avatar
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError

_SIN_PERMISO_MSG = "Solo un estudiante puede subir su propia foto de avatar."


class SubirAvatarUseCase(BaseUseCase[SubirAvatarDTO, AvatarResultDTO]):
    """Sube una imagen propia como avatar (valida MIME real + tamaño en `guardar_avatar`)."""

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        perfil_repository: IPerfilJugadorRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._perfil_repository = perfil_repository

    def _validate(self, input_dto: SubirAvatarDTO) -> None:
        if input_dto.actor_rol != "estudiante":
            raise ForbiddenError(_SIN_PERMISO_MSG)

    def _execute_domain_logic(
        self, input_dto: SubirAvatarDTO
    ) -> tuple[AvatarResultDTO, list[DomainEvent]]:
        archivo_url, _tamano_kb = guardar_avatar(
            input_dto.archivo_nombre, input_dto.archivo_contenido
        )

        perfil = self._perfil_repository.get_by_estudiante(input_dto.actor_id)
        if perfil is None:
            perfil = self._perfil_repository.add(PerfilJugador(estudiante_id=input_dto.actor_id))

        perfil.avatar_tipo = AvatarTipo.SUBIDO
        perfil.avatar_valor = archivo_url
        actualizado = self._perfil_repository.update(perfil)

        result = AvatarResultDTO(
            avatar_tipo=actualizado.avatar_tipo.value, avatar_valor=actualizado.avatar_valor
        )
        return result, []
