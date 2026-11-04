from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.application.dtos import EstadoExamenDTO, ObtenerExamenDTO
from modules.progress.application.examen_intentos import estado_examen, resolver_examen
from modules.progress.domain.repositories import IProgresoRepository
from modules.shared.domain.tiempo import ahora_utc


class ObtenerExamenQuery:
    """
    `GET /progress/{assignment_id}/exam/`: estado del examen final para el
    estudiante (intentos que le quedan, bloqueo de 24 h, si dejó uno
    abierto). No devuelve preguntas: salen solo al iniciar un intento
    (`IniciarExamenUseCase`), para que mirar el examen ya cuente como
    presentarlo. Mismas precondiciones que iniciar/entregar (todas las
    secciones completas) para no revelar que existe un examen antes de tiempo.
    """

    def __init__(
        self,
        progreso_repository: IProgresoRepository,
        laboratorio_repository: ILaboratorioRepository,
    ):
        self._progreso_repository = progreso_repository
        self._laboratorio_repository = laboratorio_repository

    def execute(self, input_dto: ObtenerExamenDTO) -> EstadoExamenDTO:
        progreso, examen, preguntas = resolver_examen(
            self._progreso_repository,
            self._laboratorio_repository,
            input_dto.asignacion_id,
            input_dto.estudiante_id,
        )
        return estado_examen(self._progreso_repository, progreso, examen.id, len(preguntas), ahora_utc())
