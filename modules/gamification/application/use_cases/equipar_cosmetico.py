from modules.gamification.application.dtos import CosmeticoDesbloqueadoResultDTO, EquiparCosmeticoDTO
from modules.gamification.domain.repositories import ICosmeticoDesbloqueadoRepository, ICosmeticoRepository
from modules.gamification.domain.value_objects import TipoCosmetico
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError

_SIN_PERMISO_MSG = "Solo un estudiante puede equipar cosméticos."
_NO_ENCONTRADO_MSG = "No tenés ese cosmético desbloqueado."


class EquiparCosmeticoUseCase(BaseUseCase[EquiparCosmeticoDTO, CosmeticoDesbloqueadoResultDTO]):
    """
    Equipa un cosmético ya desbloqueado por el estudiante. Un slot por
    tipo (hoodie, gafas, aura, etc. — se desequipa cualquier otro del
    mismo tipo antes), salvo `INSIGNIA`, que admite varias equipadas a
    la vez (como badges de GitHub).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        cosmetico_desbloqueado_repository: ICosmeticoDesbloqueadoRepository,
        cosmetico_repository: ICosmeticoRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._cosmetico_desbloqueado_repository = cosmetico_desbloqueado_repository
        self._cosmetico_repository = cosmetico_repository

    def _validate(self, input_dto: EquiparCosmeticoDTO) -> None:
        if input_dto.actor_rol != "estudiante":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        desbloqueo = self._cosmetico_desbloqueado_repository.get_by_id(
            input_dto.cosmetico_desbloqueado_id
        )
        if desbloqueo is None or desbloqueo.estudiante_id != input_dto.actor_id:
            raise NotFoundError(_NO_ENCONTRADO_MSG)

        cosmetico = self._cosmetico_repository.get_by_id(desbloqueo.cosmetico_id)
        if cosmetico is None:
            raise NotFoundError(_NO_ENCONTRADO_MSG)

        self._desbloqueo = desbloqueo
        self._cosmetico = cosmetico

    def _execute_domain_logic(
        self, input_dto: EquiparCosmeticoDTO
    ) -> tuple[CosmeticoDesbloqueadoResultDTO, list[DomainEvent]]:
        if self._cosmetico.tipo != TipoCosmetico.INSIGNIA:
            propios = self._cosmetico_desbloqueado_repository.find_por_estudiante(input_dto.actor_id)
            for otro in propios:
                if otro.id == self._desbloqueo.id or not otro.equipado:
                    continue
                otro_cosmetico = self._cosmetico_repository.get_by_id(otro.cosmetico_id)
                if otro_cosmetico is not None and otro_cosmetico.tipo == self._cosmetico.tipo:
                    otro.equipado = False
                    self._cosmetico_desbloqueado_repository.update(otro)

        self._desbloqueo.equipado = True
        actualizado = self._cosmetico_desbloqueado_repository.update(self._desbloqueo)

        result = CosmeticoDesbloqueadoResultDTO(
            id=actualizado.id, cosmetico_id=actualizado.cosmetico_id, equipado=actualizado.equipado
        )
        return result, []
