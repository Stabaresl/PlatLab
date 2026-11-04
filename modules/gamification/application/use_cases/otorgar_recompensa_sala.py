import uuid
from dataclasses import dataclass, field

from modules.gamification.application.desbloqueo import desbloquear_logro
from modules.gamification.domain.entities import (
    XP_POR_PUESTO_SALA,
    XP_SALA_POR_DEFECTO,
    Logro,
    PerfilJugador,
    RecompensaSala,
)
from modules.gamification.domain.events import LogroDesbloqueadoEvent
from modules.gamification.domain.value_objects import TipoCriterioLogro
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent


@dataclass(frozen=True)
class OtorgarRecompensaSalaDTO:
    estudiante_id: uuid.UUID
    sala_id: uuid.UUID
    posicion: int


@dataclass(frozen=True)
class RecompensaSalaResultDTO:
    xp_otorgado: int
    nivel_actual: int
    logros: list[str] = field(default_factory=list)


class OtorgarRecompensaSalaUseCase(BaseUseCase[OtorgarRecompensaSalaDTO, RecompensaSalaResultDTO]):
    """
    Lo dispara `SalaCompletadaPorEstudiante` (Rooms): suma el bono de XP por
    puesto de llegada y evalúa los logros de salas (N salas terminadas,
    primer puesto). Idempotente por `(estudiante_id, sala_id)`.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        perfil_repository,
        recompensa_repository,
        logro_repository,
        logro_desbloqueado_repository,
        cosmetico_repository,
        cosmetico_desbloqueado_repository,
        titulo_repository,
        titulo_desbloqueado_repository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._perfil_repository = perfil_repository
        self._recompensa_repository = recompensa_repository
        self._logro_repository = logro_repository
        self._logro_desbloqueado_repository = logro_desbloqueado_repository
        self._cosmetico_repository = cosmetico_repository
        self._cosmetico_desbloqueado_repository = cosmetico_desbloqueado_repository
        self._titulo_repository = titulo_repository
        self._titulo_desbloqueado_repository = titulo_desbloqueado_repository

    def _validate(self, input_dto: OtorgarRecompensaSalaDTO) -> None:
        self._ya_otorgada = self._recompensa_repository.existe(input_dto.estudiante_id, input_dto.sala_id)

    def _execute_domain_logic(
        self, input_dto: OtorgarRecompensaSalaDTO
    ) -> tuple[RecompensaSalaResultDTO, list[DomainEvent]]:
        perfil = self._perfil_repository.get_by_estudiante(input_dto.estudiante_id)
        if self._ya_otorgada:
            return RecompensaSalaResultDTO(xp_otorgado=0, nivel_actual=perfil.nivel if perfil else 1), []

        xp = XP_POR_PUESTO_SALA.get(input_dto.posicion, XP_SALA_POR_DEFECTO)
        self._recompensa_repository.add(
            RecompensaSala(
                estudiante_id=input_dto.estudiante_id,
                sala_id=input_dto.sala_id,
                posicion=input_dto.posicion,
                xp=xp,
            )
        )
        if perfil is None:
            perfil = self._perfil_repository.add(PerfilJugador(estudiante_id=input_dto.estudiante_id))
        perfil.agregar_xp(xp)
        perfil = self._perfil_repository.update(perfil)

        nuevos = self._evaluar_logros(input_dto.estudiante_id)
        eventos: list[DomainEvent] = [
            LogroDesbloqueadoEvent(estudiante_id=input_dto.estudiante_id, logro_id=lg.id, nombre=lg.nombre)
            for lg in nuevos
        ]
        return (
            RecompensaSalaResultDTO(xp_otorgado=xp, nivel_actual=perfil.nivel, logros=[lg.nombre for lg in nuevos]),
            eventos,
        )

    def _evaluar_logros(self, estudiante_id: uuid.UUID) -> list[Logro]:
        salas = self._recompensa_repository.contar_por_estudiante(estudiante_id)
        primeros = self._recompensa_repository.contar_primeros_puestos(estudiante_id)
        nuevos: list[Logro] = []
        for logro in self._logro_repository.find_todos():
            if logro.tipo_criterio == TipoCriterioLogro.SALAS_COMPLETADAS:
                cumplido = salas >= int(logro.criterio_valor or 1)
            elif logro.tipo_criterio == TipoCriterioLogro.PRIMER_PUESTO_SALA:
                cumplido = primeros >= int(logro.criterio_valor or 1)
            else:
                continue
            if not cumplido or self._logro_desbloqueado_repository.existe(estudiante_id, logro.id):
                continue
            desbloquear_logro(
                estudiante_id,
                logro,
                self._logro_desbloqueado_repository,
                self._cosmetico_repository,
                self._cosmetico_desbloqueado_repository,
                self._titulo_repository,
                self._titulo_desbloqueado_repository,
            )
            nuevos.append(logro)
        return nuevos
