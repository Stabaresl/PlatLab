import uuid

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.domain.exceptions import NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.shared.presentation.pagination import ListaPagination
from modules.users.application.dtos import (
    ActualizarUsuarioDTO,
    DeshabilitarUsuarioDTO,
    HabilitarUsuarioDTO,
    ListarUsuariosDTO,
    ObtenerDashboardAdminDTO,
    SolicitarInstructorDTO,
)
from modules.users.application.queries.listar_usuarios import ListarUsuariosQuery
from modules.users.application.queries.obtener_dashboard_admin import ObtenerDashboardAdminQuery
from modules.users.application.queries.obtener_solicitud_instructor_actual import (
    ObtenerSolicitudInstructorActualQuery,
)
from modules.users.application.queries.obtener_usuario import ObtenerUsuarioQuery
from modules.users.application.use_cases.actualizar_usuario import ActualizarUsuarioUseCase
from modules.users.application.use_cases.deshabilitar_usuario import DeshabilitarUsuarioUseCase
from modules.users.application.use_cases.habilitar_usuario import HabilitarUsuarioUseCase
from modules.users.application.use_cases.solicitar_convertirse_en_instructor import (
    SolicitarConvertirseEnInstructorUseCase,
)
from modules.users.infrastructure.repositories import SolicitudInstructorRepository, UserRepository
from modules.users.presentation.serializers import (
    ActualizarUsuarioRequestSerializer,
    ListarUsuariosQuerySerializer,
    SolicitarInstructorRequestSerializer,
)

_ID_INVALIDO_MSG = "Usuario no encontrado."


def _parsear_uuid(valor: str) -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (ValueError, TypeError, AttributeError) as exc:
        raise NotFoundError(_ID_INVALIDO_MSG) from exc


def _serializar_usuario(resultado) -> dict:
    return {
        "id": str(resultado.id),
        "email": resultado.email,
        "nombre_completo": resultado.nombre_completo,
        "rol": resultado.rol,
        "is_active": resultado.is_active,
    }


def _serializar_solicitud_instructor(resultado) -> dict:
    return {
        "id": str(resultado.id),
        "estado": resultado.estado,
        "orcid": resultado.orcid,
        "motivo_rechazo": resultado.motivo_rechazo,
        "created_at": resultado.created_at.isoformat() if resultado.created_at else None,
    }


class UserViewSet(ViewSet):
    """`/api/v1/users/` — HA-01, api.md §4. Solo Admin (validado en Application)."""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        query_serializer = ListarUsuariosQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        resultado = ListarUsuariosQuery(UserRepository()).execute(
            ListarUsuariosDTO(actor_rol=request.user.rol, **query_serializer.validated_data)
        )
        serializados = [_serializar_usuario(item) for item in resultado]
        paginator = ListaPagination()
        pagina = paginator.paginate_queryset(serializados, request, view=self)
        return paginator.get_paginated_response(pagina)

    def retrieve(self, request, pk=None):
        resultado = ObtenerUsuarioQuery(UserRepository()).execute(
            usuario_id=_parsear_uuid(pk), actor_rol=request.user.rol
        )
        return Response(_serializar_usuario(resultado), status=status.HTTP_200_OK)

    def partial_update(self, request, pk=None):
        serializer = ActualizarUsuarioRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = ActualizarUsuarioUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            user_repository=UserRepository(),
        )
        resultado = use_case.execute(
            ActualizarUsuarioDTO(
                usuario_id=_parsear_uuid(pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
                **serializer.validated_data,
            )
        )
        return Response(_serializar_usuario(resultado), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="disable")
    def disable(self, request, pk=None):
        use_case = DeshabilitarUsuarioUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            user_repository=UserRepository(),
        )
        resultado = use_case.execute(
            DeshabilitarUsuarioDTO(
                usuario_id=_parsear_uuid(pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
            )
        )
        return Response(_serializar_usuario(resultado), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="enable")
    def enable(self, request, pk=None):
        use_case = HabilitarUsuarioUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            user_repository=UserRepository(),
        )
        resultado = use_case.execute(
            HabilitarUsuarioDTO(
                usuario_id=_parsear_uuid(pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
            )
        )
        return Response(_serializar_usuario(resultado), status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="instructor-requests")
    def solicitar_instructor(self, request):
        serializer = SolicitarInstructorRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = SolicitarConvertirseEnInstructorUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            user_repository=UserRepository(),
            solicitud_repository=SolicitudInstructorRepository(),
        )
        resultado = use_case.execute(
            SolicitarInstructorDTO(
                actor_id=request.user.id,
                actor_rol=request.user.rol,
                **serializer.validated_data,
            )
        )
        return Response(_serializar_solicitud_instructor(resultado), status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="instructor-requests/mine")
    def mi_solicitud_instructor(self, request):
        resultado = ObtenerSolicitudInstructorActualQuery(SolicitudInstructorRepository()).execute(
            actor_id=request.user.id
        )
        if resultado is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(_serializar_solicitud_instructor(resultado), status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        resultado = ObtenerDashboardAdminQuery(
            user_repository=UserRepository(),
            laboratorio_repository=LaboratorioRepository(),
            asignacion_repository=AsignacionRepository(),
            progreso_repository=ProgresoRepository(),
        ).execute(ObtenerDashboardAdminDTO(actor_rol=request.user.rol))

        return Response(
            {
                "usuarios_por_rol": resultado.usuarios_por_rol,
                "laboratorios_activos": resultado.laboratorios_activos,
                "labs_mas_populares": [
                    {
                        "laboratorio_id": str(item.laboratorio_id),
                        "nombre": item.nombre,
                        "estudiantes_inscritos": item.estudiantes_inscritos,
                    }
                    for item in resultado.labs_mas_populares
                ],
                "tasa_completitud_promedio": resultado.tasa_completitud_promedio,
            },
            status=status.HTTP_200_OK,
        )
