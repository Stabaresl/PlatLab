import uuid

from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.rooms.application.dtos import LaboratorioParaSalaDTO, SalaResultDTO
from modules.rooms.application.serializacion import sala_a_dto
from modules.rooms.application.use_cases.crear_sala import laboratorio_disponible_para_sala
from modules.rooms.domain.repositories import IParticipanteSalaRepository, ISalaRepository
from modules.users.domain.repositories import IUserRepository


class ListarSalasQuery:
    """
    "Mis salas": el estudiante ve las salas donde entró (con su asignación
    para ir directo al laboratorio); el instructor, las que abrió; el admin,
    todas. Más recientes primero.
    """

    def __init__(
        self,
        sala_repository: ISalaRepository,
        participante_repository: IParticipanteSalaRepository,
        laboratorio_repository: ILaboratorioRepository,
        user_repository: IUserRepository,
    ):
        self._sala_repository = sala_repository
        self._participante_repository = participante_repository
        self._laboratorio_repository = laboratorio_repository
        self._user_repository = user_repository

    def execute(self, actor_id: uuid.UUID, actor_rol: str) -> list[SalaResultDTO]:
        mias: dict[uuid.UUID, object] = {}
        if actor_rol == "estudiante":
            participaciones = self._participante_repository.find_por_estudiante(actor_id)
            mias = {p.sala_id: p for p in participaciones}
            salas = list(self._sala_repository.get_by_ids(list(mias)).values())
        elif actor_rol == "administrador":
            salas = self._sala_repository.find_todas()
        else:
            salas = self._sala_repository.find_por_anfitrion(actor_id)

        salas.sort(key=lambda s: s.created_at, reverse=True)
        ids = [s.id for s in salas]
        conteos = self._participante_repository.contar_por_salas(ids)
        completados = {s.id: self._participante_repository.contar_completados(s.id) for s in salas}
        laboratorios = self._laboratorio_repository.get_by_ids(list({s.laboratorio_id for s in salas}))
        anfitriones = self._user_repository.get_by_ids(list({s.anfitrion_id for s in salas}))
        return [
            sala_a_dto(
                s,
                laboratorios.get(s.laboratorio_id),
                anfitriones.get(s.anfitrion_id),
                participantes=conteos.get(s.id, 0),
                completados=completados[s.id],
                mio=mias.get(s.id),
            )
            for s in salas
        ]


class ListarLaboratoriosParaSalaQuery:
    """Laboratorios sobre los que el actor puede abrir una sala (ver `laboratorio_disponible_para_sala`)."""

    def __init__(self, laboratorio_repository: ILaboratorioRepository):
        self._laboratorio_repository = laboratorio_repository

    def execute(self, actor_id: uuid.UUID, actor_rol: str) -> list[LaboratorioParaSalaDTO]:
        if actor_rol not in ("instructor", "administrador"):
            return []
        resultado = []
        for lab in self._laboratorio_repository.find_publicados():
            if not laboratorio_disponible_para_sala(lab, actor_id, actor_rol):
                continue
            secciones = len(self._laboratorio_repository.get_secciones(lab.id))
            if secciones == 0:
                continue
            resultado.append(
                LaboratorioParaSalaDTO(
                    id=lab.id,
                    nombre=lab.nombre,
                    descripcion=lab.descripcion,
                    nivel_dificultad=lab.nivel_dificultad.value,
                    tipo=lab.tipo.value,
                    secciones=secciones,
                )
            )
        resultado.sort(key=lambda lab: lab.nombre.lower())
        return resultado
