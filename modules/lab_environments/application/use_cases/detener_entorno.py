from modules.lab_environments.application.dtos import DetenerEntornoDTO
from modules.lab_environments.domain.ports import IContenedorProvider
from modules.lab_environments.domain.repositories import IEntornoRepository
from modules.shared.domain.exceptions import NotFoundError

_NO_ENCONTRADO_MSG = "Entorno no encontrado."


class DetenerEntornoUseCase:
    """
    Apagado explícito por el propio estudiante ("Detener entorno"). Sin
    eventos de dominio que despachar, así que no necesita el Template
    Method de `BaseUseCase` (mismo criterio que
    `CerrarAsignacionesVencidasUseCase`) — igual corre dentro de una
    transacción propia para que "detener en Docker" y "marcar detenido en
    la base" queden consistentes.
    """

    def __init__(
        self,
        unit_of_work,
        entorno_repository: IEntornoRepository,
        contenedor_provider: IContenedorProvider,
    ):
        self._uow = unit_of_work
        self._entorno_repository = entorno_repository
        self._contenedor_provider = contenedor_provider

    def execute(self, input_dto: DetenerEntornoDTO) -> None:
        entorno = self._entorno_repository.get_by_id(input_dto.entorno_id)
        if entorno is None or not entorno.es_propio_de(input_dto.estudiante_id):
            raise NotFoundError(_NO_ENCONTRADO_MSG)

        with self._uow:
            self._contenedor_provider.detener(entorno.container_id)
            entorno.marcar_detenido()
            self._entorno_repository.update(entorno)
            self._uow.commit()
