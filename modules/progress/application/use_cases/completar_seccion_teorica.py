import uuid

from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.application.dtos import (
    CompletarSeccionTeoricaDTO,
    CompletarSeccionTeoricaResultDTO,
)
from modules.progress.domain.entities import HistorialCompletitud
from modules.progress.domain.events import LabCompleted, SectionCompleted
from modules.progress.domain.exceptions import (
    AsignacionVencidaError,
    SeccionBloqueadaError,
    SeccionRequierePracticaError,
)
from modules.progress.domain.ports import IEstadoAsignacionProvider
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.services import GestorDeSecuencia
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import NotFoundError

_PROGRESO_NO_ENCONTRADO_MSG = "Progreso no encontrado."
_SECCION_NO_ENCONTRADA_MSG = "Sección no encontrada."
_BLOQUEADA_MSG = "Esta sección todavía está bloqueada."
_REQUIERE_PRACTICA_MSG = "Esta sección tiene práctica: completala enviando la flag correcta."
_VENCIDA_MSG = "Este laboratorio venció. Ya no se puede continuar."


class CompletarSeccionTeoricaUseCase(
    BaseUseCase[CompletarSeccionTeoricaDTO, CompletarSeccionTeoricaResultDTO]
):
    """
    UC-02 bis: dominio.md §3 describe el avance de `ProgresoSeccion` solo a
    través de `ValidarFlagUseCase` ("al completar la sección N, última flag
    resuelta, se desbloquea N+1"), pero `Seccion.tiene_practica=False`
    (ej. una introducción puramente teórica) no tiene flag que validar —
    sin este caso de uso esas secciones no tenían ninguna forma de
    completarse y el laboratorio quedaba trabado ahí para siempre. Marca
    la sección como "leída" y reutiliza el mismo `GestorDeSecuencia` que
    `ValidarFlagUseCase` para desbloquear la siguiente.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        progreso_repository: IProgresoRepository,
        laboratorio_repository: ILaboratorioRepository,
        gestor_de_secuencia: GestorDeSecuencia | None = None,
        estado_asignacion_provider: IEstadoAsignacionProvider | None = None,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._progreso_repository = progreso_repository
        self._laboratorio_repository = laboratorio_repository
        self._gestor = gestor_de_secuencia or GestorDeSecuencia()
        self._estado_asignacion_provider = estado_asignacion_provider

    def _validate(self, input_dto: CompletarSeccionTeoricaDTO) -> None:
        progreso = self._progreso_repository.get_by_asignacion(input_dto.asignacion_id)
        if progreso is None or not progreso.es_propio_de(input_dto.estudiante_id):
            raise NotFoundError(_PROGRESO_NO_ENCONTRADO_MSG)

        if self._estado_asignacion_provider is not None:
            estado = self._estado_asignacion_provider.obtener_estado(input_dto.asignacion_id)
            if estado is not None and estado.vencida:
                raise AsignacionVencidaError(_VENCIDA_MSG)

        progreso_seccion = self._progreso_repository.get_seccion(
            progreso.id, input_dto.seccion_id
        )
        if progreso_seccion is None:
            raise NotFoundError(_SECCION_NO_ENCONTRADA_MSG)
        if progreso_seccion.estado == EstadoProgresoSeccion.BLOQUEADA:
            raise SeccionBloqueadaError(_BLOQUEADA_MSG)

        seccion = self._laboratorio_repository.get_seccion_by_id(input_dto.seccion_id)
        if seccion is None:
            raise NotFoundError(_SECCION_NO_ENCONTRADA_MSG)
        if seccion.tiene_practica:
            raise SeccionRequierePracticaError(_REQUIERE_PRACTICA_MSG)

        self._progreso = progreso
        self._progreso_seccion = progreso_seccion

    def _execute_domain_logic(
        self, input_dto: CompletarSeccionTeoricaDTO
    ) -> tuple[CompletarSeccionTeoricaResultDTO, list[DomainEvent]]:
        # Idempotente: reintentar sobre una sección ya completada no debe
        # reprocesar el desbloqueo ni el historial (evita duplicados ante
        # doble click / reintento de red).
        if self._progreso_seccion.estado == EstadoProgresoSeccion.COMPLETADA:
            return CompletarSeccionTeoricaResultDTO(seccion_desbloqueada=None), []

        self._progreso_repository.tocar_actividad(self._progreso.id)

        secciones = sorted(
            self._progreso_repository.get_secciones(self._progreso.id),
            key=lambda s: self._orden_de(s.seccion_id),
        )
        modificadas = self._gestor.completar_y_desbloquear_siguiente(
            secciones, input_dto.seccion_id
        )
        for seccion in modificadas:
            self._progreso_repository.actualizar_seccion(seccion)

        seccion_desbloqueada: uuid.UUID | None = None
        if len(modificadas) > 1:
            seccion_desbloqueada = modificadas[1].seccion_id

        events: list[DomainEvent] = [
            SectionCompleted(progreso_id=self._progreso.id, seccion_id=input_dto.seccion_id)
        ]
        if self._gestor.laboratorio_completado(secciones):
            events.append(LabCompleted(progreso_id=self._progreso.id))
            self._registrar_historial_si_no_hay_examen(input_dto.seccion_id)

        return CompletarSeccionTeoricaResultDTO(seccion_desbloqueada=seccion_desbloqueada), events

    def _orden_de(self, seccion_id: uuid.UUID) -> int:
        seccion = self._laboratorio_repository.get_seccion_by_id(seccion_id)
        return seccion.orden if seccion else 0

    def _registrar_historial_si_no_hay_examen(self, seccion_id: uuid.UUID) -> None:
        """HE-11/RF-13: ver misma nota en `ValidarFlagUseCase`."""
        seccion = self._laboratorio_repository.get_seccion_by_id(seccion_id)
        if seccion is None:
            return
        if self._laboratorio_repository.get_examen_by_laboratorio(seccion.laboratorio_id):
            return

        numero_intento = len(self._progreso_repository.get_historial(self._progreso.id)) + 1
        self._progreso_repository.registrar_historial(
            HistorialCompletitud(progreso_id=self._progreso.id, numero_intento=numero_intento)
        )
