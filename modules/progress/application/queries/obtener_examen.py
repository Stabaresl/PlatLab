from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.application.dtos import (
    ExamenParaResolverDTO,
    ObtenerExamenDTO,
    PreguntaExamenItemDTO,
)
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.shared.domain.exceptions import BusinessRuleViolationError, NotFoundError

_PROGRESO_NO_ENCONTRADO_MSG = "Progreso no encontrado."
_SECCIONES_INCOMPLETAS_MSG = "Debes completar todas las secciones antes de ver el examen."
_EXAMEN_NO_CONFIGURADO_MSG = "Este laboratorio no tiene examen configurado."


class ObtenerExamenQuery:
    """
    `GET /progress/{assignment_id}/exam/`: expone las preguntas del
    examen final para que el estudiante pueda responderlas — nunca
    `respuesta_hash` (mismo bloqueo estructural que
    `ObtenerContenidoSeccionQuery` con `contenido_teorico`/flags). Mismas
    precondiciones que `EnviarExamenUseCase` (todas las secciones
    completas) para no revelar que existe un examen antes de tiempo.
    """

    def __init__(
        self,
        progreso_repository: IProgresoRepository,
        laboratorio_repository: ILaboratorioRepository,
    ):
        self._progreso_repository = progreso_repository
        self._laboratorio_repository = laboratorio_repository

    def execute(self, input_dto: ObtenerExamenDTO) -> ExamenParaResolverDTO:
        progreso = self._progreso_repository.get_by_asignacion(input_dto.asignacion_id)
        if progreso is None or not progreso.es_propio_de(input_dto.estudiante_id):
            raise NotFoundError(_PROGRESO_NO_ENCONTRADO_MSG)

        secciones = self._progreso_repository.get_secciones(progreso.id)
        if not secciones or any(s.estado != EstadoProgresoSeccion.COMPLETADA for s in secciones):
            raise BusinessRuleViolationError(_SECCIONES_INCOMPLETAS_MSG)

        primera_seccion = self._laboratorio_repository.get_seccion_by_id(secciones[0].seccion_id)
        examen = self._laboratorio_repository.get_examen_by_laboratorio(
            primera_seccion.laboratorio_id
        )
        if examen is None:
            raise BusinessRuleViolationError(_EXAMEN_NO_CONFIGURADO_MSG)

        preguntas = self._laboratorio_repository.get_preguntas(examen.id)
        return ExamenParaResolverDTO(
            examen_id=examen.id,
            preguntas=[
                PreguntaExamenItemDTO(
                    id=p.id, enunciado=p.enunciado, tipo=p.tipo.value, opciones=p.opciones
                )
                for p in preguntas
            ],
        )
