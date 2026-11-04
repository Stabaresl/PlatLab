import uuid

from django.db.models import Count

from modules.rooms.domain.entities import ParticipanteSala, Sala
from modules.rooms.domain.value_objects import EstadoSala
from modules.rooms.infrastructure.models import ParticipanteSalaModel, SalaModel


def _sala_to_entity(m: SalaModel) -> Sala:
    return Sala(
        id=m.id,
        nombre=m.nombre,
        descripcion=m.descripcion,
        laboratorio_id=m.laboratorio_id,
        anfitrion_id=m.anfitrion_id,
        codigo=m.codigo,
        capacidad=m.capacidad,
        estado=EstadoSala(m.estado),
        fecha_fin=m.fecha_fin,
        created_at=m.created_at,
    )


def _participante_to_entity(m: ParticipanteSalaModel) -> ParticipanteSala:
    return ParticipanteSala(
        id=m.id,
        sala_id=m.sala_id,
        estudiante_id=m.estudiante_id,
        asignacion_id=m.asignacion_id,
        completado_antes=m.completado_antes,
        posicion_final=m.posicion_final,
        fecha_completado=m.fecha_completado,
        unido_en=m.unido_en,
    )


class SalaRepository:
    def get_by_id(self, sala_id: uuid.UUID) -> Sala | None:
        m = SalaModel.objects.filter(id=sala_id).first()
        return _sala_to_entity(m) if m else None

    def get_by_codigo(self, codigo: str) -> Sala | None:
        if not codigo:
            return None
        m = SalaModel.objects.filter(codigo=codigo).first()
        return _sala_to_entity(m) if m else None

    def existe_codigo(self, codigo: str) -> bool:
        return SalaModel.objects.filter(codigo=codigo).exists()

    def bloquear(self, sala_id: uuid.UUID) -> Sala:
        return _sala_to_entity(SalaModel.objects.select_for_update().get(id=sala_id))

    def add(self, sala: Sala) -> Sala:
        m = SalaModel.objects.create(
            id=sala.id,
            nombre=sala.nombre,
            descripcion=sala.descripcion,
            laboratorio_id=sala.laboratorio_id,
            anfitrion_id=sala.anfitrion_id,
            codigo=sala.codigo,
            capacidad=sala.capacidad,
            estado=sala.estado.value,
            fecha_fin=sala.fecha_fin,
        )
        return _sala_to_entity(m)

    def update(self, sala: Sala) -> Sala:
        SalaModel.objects.filter(id=sala.id).update(
            nombre=sala.nombre,
            descripcion=sala.descripcion,
            capacidad=sala.capacidad,
            estado=sala.estado.value,
            fecha_fin=sala.fecha_fin,
        )
        return self.get_by_id(sala.id)

    def find_por_anfitrion(self, anfitrion_id: uuid.UUID) -> list[Sala]:
        return [_sala_to_entity(m) for m in SalaModel.objects.filter(anfitrion_id=anfitrion_id).order_by("-created_at")]

    def find_todas(self, limit: int = 200) -> list[Sala]:
        return [_sala_to_entity(m) for m in SalaModel.objects.order_by("-created_at")[:limit]]

    def get_by_ids(self, sala_ids: list[uuid.UUID]) -> dict[uuid.UUID, Sala]:
        if not sala_ids:
            return {}
        return {m.id: _sala_to_entity(m) for m in SalaModel.objects.filter(id__in=sala_ids)}


class ParticipanteSalaRepository:
    def get(self, sala_id: uuid.UUID, estudiante_id: uuid.UUID) -> ParticipanteSala | None:
        m = ParticipanteSalaModel.objects.filter(sala_id=sala_id, estudiante_id=estudiante_id).first()
        return _participante_to_entity(m) if m else None

    def add(self, participante: ParticipanteSala) -> ParticipanteSala:
        m = ParticipanteSalaModel.objects.create(
            id=participante.id,
            sala_id=participante.sala_id,
            estudiante_id=participante.estudiante_id,
            asignacion_id=participante.asignacion_id,
            completado_antes=participante.completado_antes,
            posicion_final=participante.posicion_final,
            fecha_completado=participante.fecha_completado,
        )
        return _participante_to_entity(m)

    def update(self, participante: ParticipanteSala) -> ParticipanteSala:
        ParticipanteSalaModel.objects.filter(id=participante.id).update(
            completado_antes=participante.completado_antes,
            posicion_final=participante.posicion_final,
            fecha_completado=participante.fecha_completado,
        )
        return _participante_to_entity(ParticipanteSalaModel.objects.get(id=participante.id))

    def contar(self, sala_id: uuid.UUID) -> int:
        return ParticipanteSalaModel.objects.filter(sala_id=sala_id).count()

    def contar_por_salas(self, sala_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        if not sala_ids:
            return {}
        filas = ParticipanteSalaModel.objects.filter(sala_id__in=sala_ids).values("sala_id").annotate(n=Count("id"))
        return {f["sala_id"]: f["n"] for f in filas}

    def contar_completados(self, sala_id: uuid.UUID) -> int:
        return ParticipanteSalaModel.objects.filter(sala_id=sala_id, posicion_final__isnull=False).count()

    def find_por_sala(self, sala_id: uuid.UUID) -> list[ParticipanteSala]:
        return [
            _participante_to_entity(m)
            for m in ParticipanteSalaModel.objects.filter(sala_id=sala_id).order_by("unido_en")
        ]

    def find_por_estudiante(self, estudiante_id: uuid.UUID) -> list[ParticipanteSala]:
        return [
            _participante_to_entity(m)
            for m in ParticipanteSalaModel.objects.filter(estudiante_id=estudiante_id).order_by("-unido_en")
        ]

    def find_por_asignacion(self, asignacion_id: uuid.UUID) -> list[ParticipanteSala]:
        return [_participante_to_entity(m) for m in ParticipanteSalaModel.objects.filter(asignacion_id=asignacion_id)]
