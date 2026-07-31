import uuid

from modules.gamification.application.dtos import (
    LogroDesbloqueadoResultDTO,
    ProcesarCompletitudDTO,
    ProcesarCompletitudResultDTO,
)
from modules.gamification.domain.entities import (
    XP_POR_DIFICULTAD,
    CosmeticoDesbloqueado,
    Logro,
    LogroDesbloqueado,
    PerfilJugador,
    TituloDesbloqueado,
    XpOtorgado,
)
from modules.gamification.domain.events import LogroDesbloqueadoEvent
from modules.gamification.domain.repositories import (
    ICosmeticoDesbloqueadoRepository,
    ICosmeticoRepository,
    ILogroDesbloqueadoRepository,
    ILogroRepository,
    IPerfilJugadorRepository,
    ITituloDesbloqueadoRepository,
    ITituloRepository,
    IXpOtorgadoRepository,
)
from modules.gamification.domain.value_objects import TipoCriterioLogro
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.roadmap.domain.repositories import INodoRoadmapRepository
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent

_XP_POR_DEFECTO = 50


class ProcesarCompletitudLaboratorio(
    BaseUseCase[ProcesarCompletitudDTO, ProcesarCompletitudResultDTO]
):
    """
    Orquesta lo que pasa cuando un estudiante completa de verdad un
    laboratorio (no un use case HTTP — lo llaman los listeners de
    `infrastructure/event_listeners.py`, suscritos a `ExamGraded`/
    `LabCompleted` de Progress): otorga XP (idempotente por
    `(estudiante_id, laboratorio_id)`, ver `XpOtorgado` — necesario
    porque un examen reintentable puede disparar `ExamGraded` más de
    una vez), evalúa los 3 tipos de logro y desbloquea los cosméticos
    asociados a cualquier logro nuevo.

    Compone `ILaboratorioRepository` (Laboratories) e
    `INodoRoadmapRepository` (Roadmap) directamente, mismo patrón de
    composición cross-módulo que `ListarRoadmapQuery`/
    `ObtenerDashboardAdminQuery`.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        perfil_repository: IPerfilJugadorRepository,
        xp_otorgado_repository: IXpOtorgadoRepository,
        logro_repository: ILogroRepository,
        logro_desbloqueado_repository: ILogroDesbloqueadoRepository,
        cosmetico_repository: ICosmeticoRepository,
        cosmetico_desbloqueado_repository: ICosmeticoDesbloqueadoRepository,
        titulo_repository: ITituloRepository,
        titulo_desbloqueado_repository: ITituloDesbloqueadoRepository,
        laboratorio_repository: ILaboratorioRepository,
        nodo_roadmap_repository: INodoRoadmapRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._perfil_repository = perfil_repository
        self._xp_otorgado_repository = xp_otorgado_repository
        self._logro_repository = logro_repository
        self._logro_desbloqueado_repository = logro_desbloqueado_repository
        self._cosmetico_repository = cosmetico_repository
        self._cosmetico_desbloqueado_repository = cosmetico_desbloqueado_repository
        self._titulo_repository = titulo_repository
        self._titulo_desbloqueado_repository = titulo_desbloqueado_repository
        self._laboratorio_repository = laboratorio_repository
        self._nodo_roadmap_repository = nodo_roadmap_repository

    def _validate(self, input_dto: ProcesarCompletitudDTO) -> None:
        self._ya_procesado = self._xp_otorgado_repository.existe(
            input_dto.estudiante_id, input_dto.laboratorio_id
        )
        self._laboratorio = (
            None
            if self._ya_procesado
            else self._laboratorio_repository.get_by_id(input_dto.laboratorio_id)
        )

    def _execute_domain_logic(
        self, input_dto: ProcesarCompletitudDTO
    ) -> tuple[ProcesarCompletitudResultDTO, list[DomainEvent]]:
        if self._ya_procesado or self._laboratorio is None:
            perfil = self._perfil_repository.get_by_estudiante(input_dto.estudiante_id)
            return (
                ProcesarCompletitudResultDTO(
                    xp_otorgado=0, nivel_actual=perfil.nivel if perfil else 1
                ),
                [],
            )

        xp = XP_POR_DIFICULTAD.get(self._laboratorio.nivel_dificultad.value, _XP_POR_DEFECTO)
        self._xp_otorgado_repository.add(
            XpOtorgado(
                estudiante_id=input_dto.estudiante_id,
                laboratorio_id=input_dto.laboratorio_id,
                xp=xp,
            )
        )

        perfil = self._perfil_repository.get_by_estudiante(input_dto.estudiante_id)
        if perfil is None:
            perfil = self._perfil_repository.add(PerfilJugador(estudiante_id=input_dto.estudiante_id))
        perfil.agregar_xp(xp)
        perfil = self._perfil_repository.update(perfil)

        logros_nuevos = self._evaluar_logros(input_dto.estudiante_id)

        events: list[DomainEvent] = [
            LogroDesbloqueadoEvent(estudiante_id=input_dto.estudiante_id, logro_id=l.id, nombre=l.nombre)
            for l in logros_nuevos
        ]
        result = ProcesarCompletitudResultDTO(
            xp_otorgado=xp,
            nivel_actual=perfil.nivel,
            logros_desbloqueados=[
                LogroDesbloqueadoResultDTO(logro_id=l.id, nombre=l.nombre) for l in logros_nuevos
            ],
        )
        return result, events

    def _evaluar_logros(self, estudiante_id: uuid.UUID) -> list[Logro]:
        completados_ids = self._xp_otorgado_repository.find_laboratorio_ids_por_estudiante(
            estudiante_id
        )
        total_completados = len(completados_ids)

        desbloqueados_ahora: list[Logro] = []
        for logro in self._logro_repository.find_todos():
            if self._logro_desbloqueado_repository.existe(estudiante_id, logro.id):
                continue

            cumplido = self._cumple_criterio(logro, total_completados, completados_ids)
            if not cumplido:
                continue

            self._logro_desbloqueado_repository.add(
                LogroDesbloqueado(estudiante_id=estudiante_id, logro_id=logro.id)
            )
            for cosmetico in self._cosmetico_repository.find_por_logro(logro.id):
                if not self._cosmetico_desbloqueado_repository.existe(estudiante_id, cosmetico.id):
                    self._cosmetico_desbloqueado_repository.add(
                        CosmeticoDesbloqueado(estudiante_id=estudiante_id, cosmetico_id=cosmetico.id)
                    )
            for titulo in self._titulo_repository.find_por_logro(logro.id):
                if not self._titulo_desbloqueado_repository.existe(estudiante_id, titulo.id):
                    self._titulo_desbloqueado_repository.add(
                        TituloDesbloqueado(estudiante_id=estudiante_id, titulo_id=titulo.id)
                    )
            desbloqueados_ahora.append(logro)

        return desbloqueados_ahora

    def _cumple_criterio(
        self, logro: Logro, total_completados: int, completados_ids: set[uuid.UUID]
    ) -> bool:
        if logro.tipo_criterio == TipoCriterioLogro.PRIMER_LABORATORIO:
            return total_completados >= 1
        if logro.tipo_criterio == TipoCriterioLogro.N_LABORATORIOS:
            umbral = int(logro.criterio_valor or 0)
            return total_completados >= umbral
        if logro.tipo_criterio == TipoCriterioLogro.CATEGORIA_ROADMAP_COMPLETA:
            categoria_id = uuid.UUID(logro.criterio_valor)
            nodos = self._nodo_roadmap_repository.find_por_categoria(categoria_id)
            return len(nodos) > 0 and all(n.laboratorio_id in completados_ids for n in nodos)
        return False
