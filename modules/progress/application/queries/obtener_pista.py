from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.application.dtos import ObtenerPistaDTO, PistaDTO
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.value_objects import ContadorFallos
from modules.shared.domain.exceptions import NotFoundError

_PROGRESO_NO_ENCONTRADO_MSG = "Progreso no encontrado."
_SECCION_NO_ENCONTRADA_MSG = "Sección no encontrada."
_FLAG_NO_DEFINIDA_MSG = "Esta sección todavía no tiene una flag definida."


class ObtenerPistaQuery:
    """
    HE-06, api.md §7 `GET .../hint/`: devuelve únicamente la ayuda
    progresiva ya desbloqueada según el `ContadorFallos` real de esa
    sección (5 fallos → pista, 15 → paso a paso) — nunca adelanta ayuda
    que el estudiante no se ha ganado todavía.
    """

    def __init__(
        self,
        progreso_repository: IProgresoRepository,
        laboratorio_repository: ILaboratorioRepository,
    ):
        self._progreso_repository = progreso_repository
        self._laboratorio_repository = laboratorio_repository

    def execute(self, input_dto: ObtenerPistaDTO) -> PistaDTO:
        progreso = self._progreso_repository.get_by_asignacion(input_dto.asignacion_id)
        if progreso is None or not progreso.es_propio_de(input_dto.estudiante_id):
            raise NotFoundError(_PROGRESO_NO_ENCONTRADO_MSG)

        progreso_seccion = self._progreso_repository.get_seccion(
            progreso.id, input_dto.seccion_id
        )
        if progreso_seccion is None:
            raise NotFoundError(_SECCION_NO_ENCONTRADA_MSG)

        flag = self._laboratorio_repository.get_flag_by_seccion(input_dto.seccion_id)
        if flag is None:
            raise NotFoundError(_FLAG_NO_DEFINIDA_MSG)

        fallos = self._progreso_repository.contar_fallos(progreso.id, input_dto.seccion_id)
        contador = ContadorFallos(total=fallos)

        return PistaDTO(
            intentos_fallidos=fallos,
            pista_disponible=contador.debe_mostrar_pista,
            pista=flag.ayuda.pista if contador.debe_mostrar_pista else None,
            paso_a_paso_disponible=contador.debe_mostrar_paso_a_paso,
            paso_a_paso=flag.ayuda.paso_a_paso if contador.debe_mostrar_paso_a_paso else None,
        )
