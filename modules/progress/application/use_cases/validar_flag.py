import uuid

from django.contrib.auth.hashers import check_password

from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.application.dtos import ValidarFlagDTO, ValidarFlagResultDTO
from modules.progress.domain.entities import IntentoFlag
from modules.progress.domain.events import FlagValidated, LabCompleted, SectionCompleted
from modules.progress.domain.exceptions import SeccionBloqueadaError
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.services import GestorDeSecuencia, ValidadorDeFlag
from modules.progress.domain.value_objects import ContadorFallos, EstadoProgresoSeccion
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import NotFoundError

_PROGRESO_NO_ENCONTRADO_MSG = "Progreso no encontrado."
_SECCION_NO_ENCONTRADA_MSG = "Sección no encontrada."
_FLAG_NO_DEFINIDA_MSG = "Esta sección todavía no tiene una flag definida."
_BLOQUEADA_MSG = "Esta sección todavía está bloqueada."


class ValidarFlagUseCase(BaseUseCase[ValidarFlagDTO, ValidarFlagResultDTO]):
    """
    UC-02: valida el intento de flag de un estudiante. Compara el hash
    (tiempo constante, seguridad.md §4), actualiza el `ContadorFallos` y
    la ayuda progresiva desbloqueada (HE-06), registra el intento
    (HE-07) y — si es correcta — completa la sección y desbloquea la
    siguiente (`GestorDeSecuencia`, dominio.md §3).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        progreso_repository: IProgresoRepository,
        laboratorio_repository: ILaboratorioRepository,
        validador_de_flag: ValidadorDeFlag | None = None,
        gestor_de_secuencia: GestorDeSecuencia | None = None,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._progreso_repository = progreso_repository
        self._laboratorio_repository = laboratorio_repository
        self._validador = validador_de_flag or ValidadorDeFlag()
        self._gestor = gestor_de_secuencia or GestorDeSecuencia()

    def _validate(self, input_dto: ValidarFlagDTO) -> None:
        progreso = self._progreso_repository.get_by_asignacion(input_dto.asignacion_id)
        if progreso is None or not progreso.es_propio_de(input_dto.estudiante_id):
            raise NotFoundError(_PROGRESO_NO_ENCONTRADO_MSG)

        progreso_seccion = self._progreso_repository.get_seccion(
            progreso.id, input_dto.seccion_id
        )
        if progreso_seccion is None:
            raise NotFoundError(_SECCION_NO_ENCONTRADA_MSG)
        if progreso_seccion.estado == EstadoProgresoSeccion.BLOQUEADA:
            raise SeccionBloqueadaError(_BLOQUEADA_MSG)

        flag = self._laboratorio_repository.get_flag_by_seccion(input_dto.seccion_id)
        if flag is None:
            raise NotFoundError(_FLAG_NO_DEFINIDA_MSG)

        self._progreso = progreso
        self._flag = flag

    def _execute_domain_logic(
        self, input_dto: ValidarFlagDTO
    ) -> tuple[ValidarFlagResultDTO, list[DomainEvent]]:
        correcta = check_password(input_dto.valor, self._flag.hash)
        fallos_previos = self._progreso_repository.contar_fallos(
            self._progreso.id, input_dto.seccion_id
        )
        resultado = self._validador.procesar_intento(
            correcta, ContadorFallos(total=fallos_previos)
        )

        self._progreso_repository.registrar_intento(
            IntentoFlag(
                progreso_id=self._progreso.id,
                seccion_id=input_dto.seccion_id,
                resultado=correcta,
            )
        )
        self._progreso_repository.tocar_actividad(self._progreso.id)

        events: list[DomainEvent] = [
            FlagValidated(
                progreso_id=self._progreso.id,
                seccion_id=input_dto.seccion_id,
                correcta=correcta,
            )
        ]

        seccion_desbloqueada: uuid.UUID | None = None
        if correcta:
            secciones = sorted(
                self._progreso_repository.get_secciones(self._progreso.id),
                key=lambda s: self._orden_de(s.seccion_id),
            )
            modificadas = self._gestor.completar_y_desbloquear_siguiente(
                secciones, input_dto.seccion_id
            )
            for seccion in modificadas:
                self._progreso_repository.actualizar_seccion(seccion)
            if len(modificadas) > 1:
                seccion_desbloqueada = modificadas[1].seccion_id

            events.append(
                SectionCompleted(progreso_id=self._progreso.id, seccion_id=input_dto.seccion_id)
            )
            if self._gestor.laboratorio_completado(secciones):
                events.append(LabCompleted(progreso_id=self._progreso.id))

        result = ValidarFlagResultDTO(
            correcto=correcta,
            intentos_fallidos=resultado.contador.total,
            seccion_desbloqueada=seccion_desbloqueada,
            pista_disponible=resultado.pista_desbloqueada,
            pista=self._flag.ayuda.pista if resultado.pista_desbloqueada else None,
            paso_a_paso_disponible=resultado.paso_a_paso_desbloqueado,
            paso_a_paso=(
                self._flag.ayuda.paso_a_paso if resultado.paso_a_paso_desbloqueado else None
            ),
        )
        return result, events

    def _orden_de(self, seccion_id: uuid.UUID) -> int:
        seccion = self._laboratorio_repository.get_seccion_by_id(seccion_id)
        return seccion.orden if seccion else 0
