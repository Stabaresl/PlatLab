from django.contrib.auth.hashers import check_password

from modules.laboratories.domain.entities import Pregunta
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import TipoPregunta
from modules.progress.application.dtos import EnviarExamenDTO, EnviarExamenResultDTO
from modules.progress.domain.entities import HistorialCompletitud, ResultadoExamen
from modules.progress.domain.events import ExamGraded
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.services import CalificadorDeExamen
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import (
    BusinessRuleViolationError,
    NotFoundError,
    ValidationError,
)

_PROGRESO_NO_ENCONTRADO_MSG = "Progreso no encontrado."
_SECCIONES_INCOMPLETAS_MSG = "Debes completar todas las secciones antes de enviar el examen."
_EXAMEN_NO_CONFIGURADO_MSG = "Este laboratorio no tiene examen configurado."
_PREGUNTA_DESCONOCIDA_MSG = "Las respuestas incluyen una pregunta que no pertenece a este examen."


class EnviarExamenUseCase(BaseUseCase[EnviarExamenDTO, EnviarExamenResultDTO]):
    """
    HE-09/HI-08, UC-03, api.md §7 `POST /progress/{assignment_id}/exam/`:
    califica el envío del examen final. Solo se habilita cuando todas
    las `ProgresoSeccion` están `completada` (UC-03 E1). Reintentable
    (decisión de producto confirmada): cada envío crea un
    `ResultadoExamen` y una fila `HistorialCompletitud` nuevos, con
    `numero_intento` incremental — nunca sobrescribe un intento
    anterior. La comparación por tipo de pregunta (Strategy) vive aquí
    -`_es_correcta`- porque necesita `check_password` (Django); el
    `CalificadorDeExamen` de Domain solo agrega los booleanos ya
    evaluados en un `Puntaje` (mismo límite de capas que
    `ValidarFlagUseCase`/`ValidadorDeFlag`).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        progreso_repository: IProgresoRepository,
        laboratorio_repository: ILaboratorioRepository,
        calificador: CalificadorDeExamen | None = None,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._progreso_repository = progreso_repository
        self._laboratorio_repository = laboratorio_repository
        self._calificador = calificador or CalificadorDeExamen()

    def _validate(self, input_dto: EnviarExamenDTO) -> None:
        progreso = self._progreso_repository.get_by_asignacion(input_dto.asignacion_id)
        if progreso is None or not progreso.es_propio_de(input_dto.estudiante_id):
            raise NotFoundError(_PROGRESO_NO_ENCONTRADO_MSG)

        secciones = self._progreso_repository.get_secciones(progreso.id)
        if not secciones or any(s.estado != EstadoProgresoSeccion.COMPLETADA for s in secciones):
            raise BusinessRuleViolationError(_SECCIONES_INCOMPLETAS_MSG)

        primera_seccion = self._laboratorio_repository.get_seccion_by_id(
            secciones[0].seccion_id
        )
        examen = self._laboratorio_repository.get_examen_by_laboratorio(
            primera_seccion.laboratorio_id
        )
        if examen is None:
            raise BusinessRuleViolationError(_EXAMEN_NO_CONFIGURADO_MSG)

        preguntas = self._laboratorio_repository.get_preguntas(examen.id)
        if not preguntas:
            raise BusinessRuleViolationError(_EXAMEN_NO_CONFIGURADO_MSG)

        ids_preguntas = {str(p.id) for p in preguntas}
        if not set(input_dto.respuestas.keys()) <= ids_preguntas:
            raise ValidationError(_PREGUNTA_DESCONOCIDA_MSG)

        self._progreso = progreso
        self._examen = examen
        self._preguntas = preguntas

    def _execute_domain_logic(
        self, input_dto: EnviarExamenDTO
    ) -> tuple[EnviarExamenResultDTO, list[DomainEvent]]:
        resultados = [
            self._es_correcta(pregunta, input_dto.respuestas.get(str(pregunta.id)))
            for pregunta in self._preguntas
        ]
        puntaje = self._calificador.calificar(resultados)

        self._progreso_repository.registrar_resultado_examen(
            ResultadoExamen(
                progreso_id=self._progreso.id,
                examen_id=self._examen.id,
                respuestas=input_dto.respuestas,
                puntaje=puntaje.porcentaje,
            )
        )

        numero_intento = len(self._progreso_repository.get_historial(self._progreso.id)) + 1
        self._progreso_repository.registrar_historial(
            HistorialCompletitud(
                progreso_id=self._progreso.id,
                numero_intento=numero_intento,
                puntaje=puntaje.porcentaje,
            )
        )

        result = EnviarExamenResultDTO(
            puntaje=puntaje.porcentaje,
            correctas=puntaje.correctas,
            total=puntaje.total,
            numero_intento=numero_intento,
        )
        event = ExamGraded(
            progreso_id=self._progreso.id,
            examen_id=self._examen.id,
            puntaje=puntaje.porcentaje,
        )
        return result, [event]

    def _es_correcta(self, pregunta: Pregunta, respuesta: str | None) -> bool:
        if respuesta is None:
            return False
        valor = respuesta.strip().lower() if pregunta.tipo == TipoPregunta.ABIERTA else respuesta
        return check_password(valor, pregunta.respuesta_hash)
