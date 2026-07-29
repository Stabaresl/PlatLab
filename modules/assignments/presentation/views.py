import uuid

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from modules.assignments.application.dtos import (
    AceptarInvitacionDTO,
    FiltrarEstudiantesDTO,
    InvitarEstudiantesDTO,
    ListarAsignacionesDTO,
    RechazarInvitacionDTO,
)
from modules.assignments.application.queries.filtrar_estudiantes import FiltrarEstudiantesQuery
from modules.assignments.application.queries.listar_asignaciones import ListarAsignacionesQuery
from modules.assignments.application.use_cases.aceptar_invitacion import AceptarInvitacionUseCase
from modules.assignments.application.use_cases.invitar_estudiantes import (
    InvitarEstudiantesUseCase,
)
from modules.assignments.application.use_cases.rechazar_invitacion import (
    RechazarInvitacionUseCase,
)
from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.assignments.presentation.serializers import (
    FiltrarEstudiantesQuerySerializer,
    InvitarEstudiantesRequestSerializer,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.domain.exceptions import NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.infrastructure.repositories import UserRepository

_ID_INVALIDO_MSG = "Invitación no encontrada."


def _parsear_uuid(valor: str) -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (ValueError, TypeError, AttributeError) as exc:
        raise NotFoundError(_ID_INVALIDO_MSG) from exc


def _serializar_asignacion(resultado) -> dict:
    return {
        "id": str(resultado.id),
        "laboratorio_id": str(resultado.laboratorio_id),
        "estado": resultado.estado,
    }


class InvitationViewSet(ViewSet):
    """`/api/v1/assignments/invitations/` — UC-06, api.md §6."""

    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = InvitarEstudiantesRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = InvitarEstudiantesUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            asignacion_repository=AsignacionRepository(),
            laboratorio_repository=LaboratorioRepository(),
            user_repository=UserRepository(),
        )
        resultado = use_case.execute(
            InvitarEstudiantesDTO(
                actor_id=request.user.id,
                actor_rol=request.user.rol,
                **serializer.validated_data,
            )
        )

        return Response(
            {
                "invitaciones": [
                    {
                        "identificador": item.identificador,
                        "resultado": item.resultado,
                        "asignacion_id": (
                            str(item.asignacion_id) if item.asignacion_id else None
                        ),
                    }
                    for item in resultado.invitaciones
                ]
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="accept")
    def accept(self, request, pk=None):
        use_case = AceptarInvitacionUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            asignacion_repository=AsignacionRepository(),
            laboratorio_repository=LaboratorioRepository(),
            progreso_repository=ProgresoRepository(),
        )
        resultado = use_case.execute(
            AceptarInvitacionDTO(asignacion_id=_parsear_uuid(pk), estudiante_id=request.user.id)
        )
        return Response(_serializar_asignacion(resultado), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        use_case = RechazarInvitacionUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            asignacion_repository=AsignacionRepository(),
        )
        resultado = use_case.execute(
            RechazarInvitacionDTO(asignacion_id=_parsear_uuid(pk), estudiante_id=request.user.id)
        )
        return Response(_serializar_asignacion(resultado), status=status.HTTP_200_OK)


class AssignmentViewSet(ViewSet):
    """`/api/v1/assignments/` — listado propio + filtro de estudiantes (HI-04)."""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        resultado = ListarAsignacionesQuery(AsignacionRepository()).execute(
            ListarAsignacionesDTO(actor_id=request.user.id, actor_rol=request.user.rol)
        )
        return Response(
            [
                {
                    "id": str(item.id),
                    "estudiante_id": str(item.estudiante_id),
                    "laboratorio_id": str(item.laboratorio_id),
                    "estado": item.estado,
                    "fecha_invitacion": item.fecha_invitacion.isoformat(),
                    "fecha_vencimiento": (
                        item.fecha_vencimiento.isoformat() if item.fecha_vencimiento else None
                    ),
                }
                for item in resultado
            ],
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="students")
    def students(self, request):
        query_serializer = FiltrarEstudiantesQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        resultado = FiltrarEstudiantesQuery(
            asignacion_repository=AsignacionRepository(),
            user_repository=UserRepository(),
            progreso_repository=ProgresoRepository(),
        ).execute(
            FiltrarEstudiantesDTO(
                instructor_id=request.user.id,
                actor_rol=request.user.rol,
                **query_serializer.validated_data,
            )
        )

        return Response(
            [
                {
                    "estudiante_id": str(item.estudiante_id),
                    "nombre_completo": item.nombre_completo,
                    "laboratorio_id": str(item.laboratorio_id),
                    "estado_asignacion": item.estado_asignacion,
                    "porcentaje_completitud": item.porcentaje_completitud,
                }
                for item in resultado
            ],
            status=status.HTTP_200_OK,
        )
