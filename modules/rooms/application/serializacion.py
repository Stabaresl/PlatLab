from modules.rooms.application.dtos import SalaResultDTO
from modules.rooms.domain.entities import ParticipanteSala, Sala


def sala_a_dto(
    sala: Sala,
    laboratorio,
    anfitrion,
    participantes: int,
    completados: int,
    mio: ParticipanteSala | None = None,
) -> SalaResultDTO:
    """Arma el DTO de una sala a partir de las entidades ya cargadas en lote."""
    return SalaResultDTO(
        id=sala.id,
        nombre=sala.nombre,
        descripcion=sala.descripcion,
        codigo=sala.codigo,
        laboratorio_id=sala.laboratorio_id,
        laboratorio_nombre=laboratorio.nombre if laboratorio else "Laboratorio no disponible",
        laboratorio_nivel=laboratorio.nivel_dificultad.value if laboratorio else "",
        anfitrion_id=sala.anfitrion_id,
        anfitrion_nombre=anfitrion.nombre_completo if anfitrion else "—",
        capacidad=sala.capacidad,
        participantes=participantes,
        completados=completados,
        estado=sala.estado.value,
        acepta_ingresos=sala.acepta_ingresos(),
        fecha_fin=sala.fecha_fin,
        created_at=sala.created_at,
        mi_asignacion_id=mio.asignacion_id if mio else None,
        mi_posicion_final=mio.posicion_final if mio else None,
    )
