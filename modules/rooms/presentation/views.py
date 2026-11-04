import uuid

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.rooms.application.dtos import CambiarEstadoSalaDTO, CrearSalaDTO, UnirseSalaDTO
from modules.rooms.application.queries.detalle_sala import DetalleSalaQuery, VistaPreviaSalaQuery
from modules.rooms.application.queries.listar_salas import ListarLaboratoriosParaSalaQuery, ListarSalasQuery
from modules.rooms.application.use_cases.cambiar_estado_sala import CambiarEstadoSalaUseCase
from modules.rooms.application.use_cases.crear_sala import CrearSalaUseCase
from modules.rooms.application.use_cases.unirse_sala import UnirseSalaUseCase
from modules.rooms.infrastructure.rate_limiter import CodigoSalaRateLimiter
from modules.rooms.infrastructure.repositories import ParticipanteSalaRepository, SalaRepository
from modules.rooms.presentation.serializers import (
    CambiarEstadoSalaRequestSerializer,
    CrearSalaRequestSerializer,
    UnirseSalaRequestSerializer,
)
from modules.shared.domain.exceptions import NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.infrastructure.repositories import UserRepository


def _iso(valor):
    return valor.isoformat() if valor else None


def _uuid(valor: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, TypeError, AttributeError) as exc:
        raise NotFoundError("Sala no encontrada.") from exc


def _sala(dto) -> dict:
    return {
        "id": str(dto.id),
        "nombre": dto.nombre,
        "descripcion": dto.descripcion,
        "codigo": dto.codigo,
        "laboratorio": {
            "id": str(dto.laboratorio_id),
            "nombre": dto.laboratorio_nombre,
            "nivel": dto.laboratorio_nivel,
        },
        "anfitrion": {"id": str(dto.anfitrion_id), "nombre": dto.anfitrion_nombre},
        "capacidad": dto.capacidad,
        "participantes": dto.participantes,
        "completados": dto.completados,
        "estado": dto.estado,
        "acepta_ingresos": dto.acepta_ingresos,
        "fecha_fin": _iso(dto.fecha_fin),
        "created_at": _iso(dto.created_at),
        "mi_asignacion_id": str(dto.mi_asignacion_id) if dto.mi_asignacion_id else None,
        "mi_posicion_final": dto.mi_posicion_final,
    }


def _participante(p) -> dict:
    return {
        "estudiante_id": str(p.estudiante_id),
        "nombre": p.nombre,
        "puesto": p.puesto,
        "secciones_completadas": p.secciones_completadas,
        "secciones_total": p.secciones_total,
        "porcentaje": p.porcentaje,
        "mejor_puntaje": p.mejor_puntaje,
        "completado": p.completado,
        "completado_antes": p.completado_antes,
        "posicion_final": p.posicion_final,
        "fecha_completado": _iso(p.fecha_completado),
        "ultima_actividad": _iso(p.ultima_actividad),
        "unido_en": _iso(p.unido_en),
        "es_yo": p.es_yo,
    }


def _repos():
    return SalaRepository(), ParticipanteSalaRepository(), LaboratorioRepository(), UserRepository()


class SalaViewSet(ViewSet):
    """
    `/api/v1/salas/` — salas privadas. Instructores y admins las crean sobre
    un laboratorio publicado; los estudiantes entran con el código y cada uno
    trabaja con su propia asignación y su propio contenedor.
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        salas, participantes, laboratorios, usuarios = _repos()
        resultado = ListarSalasQuery(salas, participantes, laboratorios, usuarios).execute(
            actor_id=request.user.id, actor_rol=request.user.rol
        )
        return Response([_sala(s) for s in resultado])

    def create(self, request):
        serializer = CrearSalaRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resultado = CrearSalaUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            sala_repository=SalaRepository(),
            laboratorio_repository=LaboratorioRepository(),
            user_repository=UserRepository(),
        ).execute(CrearSalaDTO(actor_id=request.user.id, actor_rol=request.user.rol, **serializer.validated_data))
        return Response(_sala(resultado), status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        salas, participantes, laboratorios, usuarios = _repos()
        detalle = DetalleSalaQuery(salas, participantes, laboratorios, ProgresoRepository(), usuarios).execute(
            sala_id=_uuid(pk), actor_id=request.user.id, actor_rol=request.user.rol
        )
        return Response(
            {
                **_sala(detalle.sala),
                "es_anfitrion": detalle.es_anfitrion,
                "mi_asignacion_id": str(detalle.mi_asignacion_id) if detalle.mi_asignacion_id else None,
                "tablero": [_participante(p) for p in detalle.participantes],
            }
        )

    @action(detail=False, methods=["post"], url_path="unirse")
    def unirse(self, request):
        serializer = UnirseSalaRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        CodigoSalaRateLimiter().verificar(request.user.id)
        resultado = UnirseSalaUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            sala_repository=SalaRepository(),
            participante_repository=ParticipanteSalaRepository(),
            asignacion_repository=AsignacionRepository(),
            laboratorio_repository=LaboratorioRepository(),
            progreso_repository=ProgresoRepository(),
        ).execute(UnirseSalaDTO(actor_id=request.user.id, actor_rol=request.user.rol, **serializer.validated_data))
        return Response(
            {
                "sala_id": str(resultado.sala_id),
                "asignacion_id": str(resultado.asignacion_id),
                "ya_era_participante": resultado.ya_era_participante,
                "completado_antes": resultado.completado_antes,
            },
            status=status.HTTP_200_OK if resultado.ya_era_participante else status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path=r"codigo/(?P<codigo>[A-Za-z0-9-]{1,20})")
    def vista_previa(self, request, codigo=None):
        CodigoSalaRateLimiter().verificar(request.user.id)
        salas, participantes, laboratorios, usuarios = _repos()
        p = VistaPreviaSalaQuery(salas, participantes, laboratorios, usuarios).execute(
            codigo=codigo, actor_id=request.user.id
        )
        return Response(
            {
                "codigo": p.codigo,
                "nombre": p.nombre,
                "descripcion": p.descripcion,
                "laboratorio": {"nombre": p.laboratorio_nombre, "nivel": p.laboratorio_nivel},
                "anfitrion": p.anfitrion_nombre,
                "capacidad": p.capacidad,
                "participantes": p.participantes,
                "acepta_ingresos": p.acepta_ingresos,
                "ya_participo": p.ya_participo,
                "sala_id": str(p.sala_id) if p.sala_id else None,
            }
        )

    @action(detail=True, methods=["post"], url_path="estado")
    def estado(self, request, pk=None):
        serializer = CambiarEstadoSalaRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nuevo = CambiarEstadoSalaUseCase(
            unit_of_work=BaseUnitOfWork(), event_dispatcher=EventDispatcher(), sala_repository=SalaRepository()
        ).execute(
            CambiarEstadoSalaDTO(
                sala_id=_uuid(pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
                estado=serializer.validated_data["estado"],
            )
        )
        return Response({"estado": nuevo})

    @action(detail=False, methods=["get"], url_path="laboratorios-disponibles")
    def laboratorios_disponibles(self, request):
        resultado = ListarLaboratoriosParaSalaQuery(LaboratorioRepository()).execute(
            actor_id=request.user.id, actor_rol=request.user.rol
        )
        return Response(
            [
                {
                    "id": str(lab.id),
                    "nombre": lab.nombre,
                    "descripcion": lab.descripcion,
                    "nivel_dificultad": lab.nivel_dificultad,
                    "tipo": lab.tipo,
                    "secciones": lab.secciones,
                }
                for lab in resultado
            ]
        )
