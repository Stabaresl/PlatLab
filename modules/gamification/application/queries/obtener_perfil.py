import uuid

from modules.gamification.application.dtos import (
    CosmeticoPerfilItemDTO,
    LogroPerfilItemDTO,
    PerfilJugadorDTO,
    TituloPerfilItemDTO,
)
from modules.gamification.domain.entities import PerfilJugador
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
from modules.roadmap.domain.repositories import INodoRoadmapRepository
from modules.shared.domain.exceptions import ForbiddenError

_SIN_PERMISO_MSG = "Solo un estudiante tiene perfil de progresión."


class ObtenerPerfilQuery:
    """Perfil propio: XP/nivel, logros (desbloqueados + bloqueados con progreso visible) y cosméticos."""

    def __init__(
        self,
        perfil_repository: IPerfilJugadorRepository,
        xp_otorgado_repository: IXpOtorgadoRepository,
        logro_repository: ILogroRepository,
        logro_desbloqueado_repository: ILogroDesbloqueadoRepository,
        cosmetico_repository: ICosmeticoRepository,
        cosmetico_desbloqueado_repository: ICosmeticoDesbloqueadoRepository,
        titulo_repository: ITituloRepository,
        titulo_desbloqueado_repository: ITituloDesbloqueadoRepository,
        nodo_roadmap_repository: INodoRoadmapRepository,
    ):
        self._perfil_repository = perfil_repository
        self._xp_otorgado_repository = xp_otorgado_repository
        self._logro_repository = logro_repository
        self._logro_desbloqueado_repository = logro_desbloqueado_repository
        self._cosmetico_repository = cosmetico_repository
        self._cosmetico_desbloqueado_repository = cosmetico_desbloqueado_repository
        self._titulo_repository = titulo_repository
        self._titulo_desbloqueado_repository = titulo_desbloqueado_repository
        self._nodo_roadmap_repository = nodo_roadmap_repository

    def execute(self, estudiante_id: uuid.UUID, actor_rol: str) -> PerfilJugadorDTO:
        if actor_rol != "estudiante":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        perfil = self._perfil_repository.get_by_estudiante(estudiante_id) or PerfilJugador(
            estudiante_id=estudiante_id
        )
        completados_ids = self._xp_otorgado_repository.find_laboratorio_ids_por_estudiante(estudiante_id)
        total_completados = len(completados_ids)
        desbloqueados = {
            d.logro_id for d in self._logro_desbloqueado_repository.find_por_estudiante(estudiante_id)
        }

        logros = [
            self._a_logro_item(logro, logro.id in desbloqueados, total_completados, completados_ids)
            for logro in self._logro_repository.find_todos()
        ]

        cosmeticos = []
        for desbloqueo in self._cosmetico_desbloqueado_repository.find_por_estudiante(estudiante_id):
            cosmetico = self._cosmetico_repository.get_by_id(desbloqueo.cosmetico_id)
            if cosmetico is None:
                continue
            cosmeticos.append(
                CosmeticoPerfilItemDTO(
                    id=desbloqueo.id,
                    cosmetico_id=cosmetico.id,
                    clave=cosmetico.clave,
                    nombre=cosmetico.nombre,
                    tipo=cosmetico.tipo.value,
                    rareza=cosmetico.rareza.value,
                    color=cosmetico.color,
                    equipado=desbloqueo.equipado,
                )
            )

        titulos = []
        for desbloqueo in self._titulo_desbloqueado_repository.find_por_estudiante(estudiante_id):
            titulo = self._titulo_repository.get_by_id(desbloqueo.titulo_id)
            if titulo is None:
                continue
            titulos.append(
                TituloPerfilItemDTO(
                    id=desbloqueo.id,
                    titulo_id=titulo.id,
                    clave=titulo.clave,
                    nombre=titulo.nombre,
                    descripcion=titulo.descripcion,
                    rareza=titulo.rareza.value,
                    equipado=desbloqueo.equipado,
                )
            )

        return PerfilJugadorDTO(
            estudiante_id=estudiante_id,
            xp=perfil.xp,
            nivel=perfil.nivel,
            xp_para_siguiente_nivel=perfil.xp_para_siguiente_nivel(),
            avatar_tipo=perfil.avatar_tipo.value,
            avatar_valor=perfil.avatar_valor,
            logros=logros,
            cosmeticos=cosmeticos,
            titulos=titulos,
        )

    def _a_logro_item(self, logro, desbloqueado, total_completados, completados_ids) -> LogroPerfilItemDTO:
        progreso = None
        if not desbloqueado:
            if logro.tipo_criterio == TipoCriterioLogro.N_LABORATORIOS:
                umbral = int(logro.criterio_valor or 0)
                progreso = f"{min(total_completados, umbral)}/{umbral}"
            elif logro.tipo_criterio == TipoCriterioLogro.CATEGORIA_ROADMAP_COMPLETA:
                categoria_id = uuid.UUID(logro.criterio_valor)
                nodos = self._nodo_roadmap_repository.find_por_categoria(categoria_id)
                si_completados = sum(1 for n in nodos if n.laboratorio_id in completados_ids)
                progreso = f"{si_completados}/{len(nodos)}"

        return LogroPerfilItemDTO(
            id=logro.id,
            clave=logro.clave,
            nombre=logro.nombre,
            descripcion=logro.descripcion,
            rareza=logro.rareza.value,
            desbloqueado=desbloqueado,
            fecha_desbloqueo=None,
            progreso=progreso,
        )
