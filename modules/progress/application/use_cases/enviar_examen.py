from dataclasses import replace

from modules.laboratories.domain.entities import Pregunta
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import TipoPregunta
from modules.progress.application.dtos import EnviarExamenDTO, EnviarExamenResultDTO
from modules.progress.application.examen_intentos import estado_examen, registrar_intento, resolver_examen
from modules.progress.domain.exceptions import (
    AsignacionVencidaError,
    ExamenBloqueadoError,
    ExamenNoIniciadoError,
)
from modules.progress.domain.ports import IEstadoAsignacionProvider
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.services import CalificadorDeExamen
from modules.progress.domain.value_objects import PUNTAJE_APROBACION
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ValidationError
from modules.shared.domain.tiempo import ahora_utc
from modules.shared.infrastructure.secret_hasher import verificar_secreto

_PREGUNTA_DESCONOCIDA_MSG = "Las respuestas incluyen una pregunta que no pertenece a este examen."
_VENCIDA_MSG = "Este laboratorio venció. Ya no se puede continuar."
_NO_INICIADO_MSG = "Inicia el examen antes de entregarlo (o ese intento ya se cerró)."
_BLOQUEADO_MSG = "Reprobaste los 3 intentos. Podrás volver a presentar el examen 24 horas después del último."


class EnviarExamenUseCase(BaseUseCase[EnviarExamenDTO, EnviarExamenResultDTO]):
    """
    HE-09/HI-08, UC-03, api.md §7 `POST /progress/{assignment_id}/exam/`:
    califica la entrega del intento abierto con `IniciarExamenUseCase`. Solo
    se habilita cuando todas las `ProgresoSeccion` están `completada` (UC-03
    E1). Cada entrega crea un `ResultadoExamen` y una fila
    `HistorialCompletitud` nuevos (`numero_intento` incremental, nunca
    sobrescribe) y cierra el intento. Rige `PoliticaDeIntentosExamen`: 3
    intentos; tras 3 reprobados, 24 h de espera.

    La comparación por tipo de pregunta (Strategy) vive aquí -`_es_correcta`-
    porque necesita `verificar_secreto` (Infrastructure); el
    `CalificadorDeExamen` de Domain solo agrega los booleanos ya evaluados en
    un `Puntaje` (mismo límite de capas que `ValidarFlagUseCase`).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        progreso_repository: IProgresoRepository,
        laboratorio_repository: ILaboratorioRepository,
        calificador: CalificadorDeExamen | None = None,
        estado_asignacion_provider: IEstadoAsignacionProvider | None = None,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._progreso_repository = progreso_repository
        self._laboratorio_repository = laboratorio_repository
        self._calificador = calificador or CalificadorDeExamen()
        self._estado_asignacion_provider = estado_asignacion_provider

    def _validate(self, input_dto: EnviarExamenDTO) -> None:
        def _vigente():
            if self._estado_asignacion_provider is not None:
                estado = self._estado_asignacion_provider.obtener_estado(input_dto.asignacion_id)
                if estado is not None and estado.vencida:
                    raise AsignacionVencidaError(_VENCIDA_MSG)

        self._progreso, self._examen, self._preguntas = resolver_examen(
            self._progreso_repository,
            self._laboratorio_repository,
            input_dto.asignacion_id,
            input_dto.estudiante_id,
            verificar_vigencia=_vigente,
        )

        ids_preguntas = {str(p.id) for p in self._preguntas}
        if not set(input_dto.respuestas.keys()) <= ids_preguntas:
            raise ValidationError(_PREGUNTA_DESCONOCIDA_MSG)

    def _execute_domain_logic(
        self, input_dto: EnviarExamenDTO
    ) -> tuple[EnviarExamenResultDTO, list[DomainEvent]]:
        repo = self._progreso_repository
        # Bloqueo de fila: dos entregas simultáneas del mismo intento no cuentan doble.
        progreso = repo.bloquear(self._progreso.id)
        if not progreso.tiene_examen_abierto:
            raise ExamenNoIniciadoError(_NO_INICIADO_MSG)

        # El intento abierto todavía no está calificado: el estado previo se mira sin él.
        previo = estado_examen(
            repo, _sin_intento_abierto(progreso), self._examen.id, len(self._preguntas), ahora_utc()
        )
        if previo.bloqueado_hasta is not None:
            raise ExamenBloqueadoError(_BLOQUEADO_MSG)

        resultados = [
            self._es_correcta(pregunta, input_dto.respuestas.get(str(pregunta.id)))
            for pregunta in self._preguntas
        ]
        puntaje = self._calificador.calificar(resultados)
        numero_intento, evento = registrar_intento(
            repo, progreso.id, self._examen.id, input_dto.respuestas, puntaje.porcentaje
        )

        despues = estado_examen(
            repo, repo.bloquear(progreso.id), self._examen.id, len(self._preguntas), ahora_utc()
        )
        result = EnviarExamenResultDTO(
            puntaje=puntaje.porcentaje,
            correctas=puntaje.correctas,
            total=puntaje.total,
            numero_intento=numero_intento,
            aprobado=puntaje.porcentaje >= PUNTAJE_APROBACION,
            estado=despues,
        )
        return result, [evento]

    def _es_correcta(self, pregunta: Pregunta, respuesta: str | None) -> bool:
        if respuesta is None:
            return False
        valor = respuesta.strip().lower() if pregunta.tipo == TipoPregunta.ABIERTA else respuesta
        return verificar_secreto(valor, pregunta.respuesta_hash)


def _sin_intento_abierto(progreso):
    return replace(progreso, examen_iniciado_en=None)
