import uuid

from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.domain.repositories import IProgresoRepository
from modules.rooms.application.dtos import DetalleSalaDTO, ParticipanteTableroDTO, VistaPreviaSalaDTO
from modules.rooms.application.serializacion import sala_a_dto
from modules.rooms.domain.exceptions import SalaNoEncontradaError
from modules.rooms.domain.repositories import IParticipanteSalaRepository, ISalaRepository
from modules.rooms.domain.value_objects import normalizar_codigo
from modules.shared.domain.exceptions import NotFoundError
from modules.users.domain.repositories import IUserRepository

_NO_ENCONTRADA_MSG = "Sala no encontrada."


def _orden_tablero(fila: dict) -> tuple:
    """
    Primero quienes terminaron dentro de la sala (por puesto), luego los que
    van en camino (más avance, mejor examen, más antiguos en la sala) y al
    final quienes ya lo habían terminado antes de entrar.
    """
    if fila["completado_antes"]:
        return (2, 0, 0, 0, fila["unido_en"].timestamp())
    if fila["posicion_final"] is not None:
        return (0, fila["posicion_final"], 0, 0, 0)
    return (1, -fila["porcentaje"], -(fila["mejor_puntaje"] or 0), 0, fila["unido_en"].timestamp())


class DetalleSalaQuery:
    """
    Tablero de la sala: datos de la sala + cada participante con su avance
    real (secciones, examen, si terminó y en qué puesto). Lo ve el anfitrión,
    un admin o cualquier participante (el tablero es parte del juego); para
    el resto la sala "no existe".
    """

    def __init__(
        self,
        sala_repository: ISalaRepository,
        participante_repository: IParticipanteSalaRepository,
        laboratorio_repository: ILaboratorioRepository,
        progreso_repository: IProgresoRepository,
        user_repository: IUserRepository,
    ):
        self._sala_repository = sala_repository
        self._participante_repository = participante_repository
        self._laboratorio_repository = laboratorio_repository
        self._progreso_repository = progreso_repository
        self._user_repository = user_repository

    def execute(self, sala_id: uuid.UUID, actor_id: uuid.UUID, actor_rol: str) -> DetalleSalaDTO:
        sala = self._sala_repository.get_by_id(sala_id)
        if sala is None:
            raise NotFoundError(_NO_ENCONTRADA_MSG)
        participantes = self._participante_repository.find_por_sala(sala.id)
        mio = next((p for p in participantes if p.estudiante_id == actor_id), None)
        es_anfitrion = sala.anfitrion_id == actor_id
        if not (es_anfitrion or actor_rol == "administrador" or mio is not None):
            raise NotFoundError(_NO_ENCONTRADA_MSG)

        laboratorio = self._laboratorio_repository.get_by_id(sala.laboratorio_id)
        total_secciones = len(self._laboratorio_repository.get_secciones(sala.laboratorio_id))
        resumenes = self._progreso_repository.resumen_por_asignaciones([p.asignacion_id for p in participantes])
        usuarios = self._user_repository.get_by_ids(
            list({p.estudiante_id for p in participantes} | {sala.anfitrion_id})
        )

        filas = []
        for p in participantes:
            r = resumenes.get(p.asignacion_id, {})
            total = r.get("secciones_total") or total_secciones
            hechas = r.get("secciones_completadas", 0)
            usuario = usuarios.get(p.estudiante_id)
            filas.append(
                {
                    "estudiante_id": p.estudiante_id,
                    "nombre": usuario.nombre_completo if usuario else "Estudiante",
                    "secciones_completadas": hechas,
                    "secciones_total": total,
                    "porcentaje": round(hechas / total * 100) if total else 0,
                    "mejor_puntaje": r.get("mejor_puntaje"),
                    "completado": p.posicion_final is not None or bool(r.get("completado")),
                    "completado_antes": p.completado_antes,
                    "posicion_final": p.posicion_final,
                    "fecha_completado": p.fecha_completado or r.get("fecha_completado"),
                    "ultima_actividad": r.get("ultima_actividad"),
                    "unido_en": p.unido_en,
                    "es_yo": p.estudiante_id == actor_id,
                }
            )
        filas.sort(key=_orden_tablero)

        completados = sum(1 for p in participantes if p.posicion_final is not None)
        return DetalleSalaDTO(
            sala=sala_a_dto(
                sala,
                laboratorio,
                usuarios.get(sala.anfitrion_id),
                participantes=len(participantes),
                completados=completados,
                mio=mio,
            ),
            es_anfitrion=es_anfitrion or actor_rol == "administrador",
            participantes=[ParticipanteTableroDTO(puesto=i + 1, **fila) for i, fila in enumerate(filas)],
            mi_asignacion_id=mio.asignacion_id if mio else None,
        )


class VistaPreviaSalaQuery:
    """Lo que ve un estudiante antes de entrar con un código: de qué se trata y si hay cupo."""

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

    def execute(self, codigo: str, actor_id: uuid.UUID) -> VistaPreviaSalaDTO:
        sala = self._sala_repository.get_by_codigo(normalizar_codigo(codigo))
        if sala is None:
            raise SalaNoEncontradaError()
        laboratorio = self._laboratorio_repository.get_by_id(sala.laboratorio_id)
        anfitrion = self._user_repository.get_by_id(sala.anfitrion_id)
        ya_participo = self._participante_repository.get(sala.id, actor_id) is not None
        return VistaPreviaSalaDTO(
            codigo=sala.codigo,
            nombre=sala.nombre,
            descripcion=sala.descripcion,
            laboratorio_nombre=laboratorio.nombre if laboratorio else "",
            laboratorio_nivel=laboratorio.nivel_dificultad.value if laboratorio else "",
            anfitrion_nombre=anfitrion.nombre_completo if anfitrion else "—",
            capacidad=sala.capacidad,
            participantes=self._participante_repository.contar(sala.id),
            acepta_ingresos=sala.acepta_ingresos(),
            ya_participo=ya_participo,
            sala_id=sala.id if ya_participo else None,
        )
