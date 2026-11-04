from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.application.dtos import ExamenIniciadoDTO, IniciarExamenDTO, PreguntaExamenItemDTO
from modules.progress.application.examen_intentos import (
    RESPUESTAS_ABANDONO,
    estado_examen,
    registrar_intento,
    resolver_examen,
)
from modules.progress.domain.exceptions import AsignacionVencidaError
from modules.progress.domain.ports import IEstadoAsignacionProvider
from modules.progress.domain.repositories import IProgresoRepository
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.tiempo import ahora_utc

_VENCIDA_MSG = "Este laboratorio venció. Ya no se puede presentar el examen."


class IniciarExamenUseCase(BaseUseCase[IniciarExamenDTO, ExamenIniciadoDTO]):
    """
    `POST /progress/{assignment_id}/exam/iniciar/`: abre un intento del
    examen final y entrega las preguntas.

    - Si había un intento abierto (el estudiante salió sin entregar), se
      cierra primero como reprobado con 0: salir del examen cuenta como
      presentarlo.
    - Si con eso el ciclo de 3 intentos queda reprobado, no se abre uno
      nuevo: se devuelve `iniciado=False` con la hora de desbloqueo (el
      cierre del abandono sí queda guardado).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        progreso_repository: IProgresoRepository,
        laboratorio_repository: ILaboratorioRepository,
        estado_asignacion_provider: IEstadoAsignacionProvider | None = None,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._progreso_repository = progreso_repository
        self._laboratorio_repository = laboratorio_repository
        self._estado_asignacion_provider = estado_asignacion_provider

    def _validate(self, input_dto: IniciarExamenDTO) -> None:
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

    def _execute_domain_logic(self, input_dto: IniciarExamenDTO) -> tuple[ExamenIniciadoDTO, list[DomainEvent]]:
        repo = self._progreso_repository
        progreso = repo.bloquear(self._progreso.id)
        eventos: list[DomainEvent] = []
        abandono = progreso.tiene_examen_abierto
        if abandono:
            _, evento = registrar_intento(repo, progreso.id, self._examen.id, RESPUESTAS_ABANDONO, 0.0)
            eventos.append(evento)
            progreso = repo.bloquear(progreso.id)

        ahora = ahora_utc()
        estado = estado_examen(repo, progreso, self._examen.id, len(self._preguntas), ahora)
        if estado.bloqueado_hasta is not None:
            return ExamenIniciadoDTO(iniciado=False, estado=estado, preguntas=[], abandono_cerrado=abandono), eventos

        repo.fijar_examen_iniciado(progreso.id, ahora)
        preguntas = [
            PreguntaExamenItemDTO(id=p.id, enunciado=p.enunciado, tipo=p.tipo.value, opciones=p.opciones)
            for p in self._preguntas
        ]
        iniciado = ExamenIniciadoDTO(
            iniciado=True, estado=estado, preguntas=preguntas, iniciado_en=ahora, abandono_cerrado=abandono
        )
        return iniciado, eventos
