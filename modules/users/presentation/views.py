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
from modules.shared.presentation.pagination import parametros_pagina, respuesta_paginada
from modules.users.application.dtos import (
    ActualizarUsuarioDTO,
    DeshabilitarUsuarioDTO,
    HabilitarUsuarioDTO,
    ListarUsuariosDTO,
    ObtenerDashboardAdminDTO,
    ResolverSolicitudInstructorDTO,
    SolicitarInstructorDTO,
)
from modules.users.application.queries.listar_solicitudes_instructor import (
    ListarSolicitudesInstructorQuery,
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
from modules.users.application.use_cases.resolver_solicitud_instructor import (
    ResolverSolicitudInstructorUseCase,
)
from modules.users.application.use_cases.solicitar_convertirse_en_instructor import (
    SolicitarConvertirseEnInstructorUseCase,
)
from modules.users.infrastructure.repositories import SolicitudInstructorRepository, UserRepository
from modules.users.presentation.serializers import (
    ActualizarUsuarioRequestSerializer,
    ListarUsuariosQuerySerializer,
    ResolverSolicitudInstructorRequestSerializer,
    SolicitarInstructorRequestSerializer,
)

_ID_INVALIDO_MSG = "Usuario no encontrado."


def _parsear_uuid(valor: str) -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (ValueError, TypeError, AttributeError) as exc:
        raise NotFoundError(_ID_INVALIDO_MSG) from exc


def _serializar_usuario(resultado) -> dict:
    datos = {
        "id": str(resultado.id),
        "email": resultado.email,
        "nombre_completo": resultado.nombre_completo,
        "rol": resultado.rol,
        "is_active": resultado.is_active,
    }
    # Solo el listado trae fechas (tabla de usuarios del panel del admin).
    for campo in ("date_joined", "last_login"):
        if hasattr(resultado, campo):
            valor = getattr(resultado, campo)
            datos[campo] = valor.isoformat() if valor else None
    return datos


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

        limit, offset = parametros_pagina(request)
        resultado, total = ListarUsuariosQuery(UserRepository()).execute_paginado(
            ListarUsuariosDTO(actor_rol=request.user.rol, **query_serializer.validated_data),
            limit=limit,
            offset=offset,
        )
        return respuesta_paginada(
            request, [_serializar_usuario(item) for item in resultado], total, limit, offset
        )

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

    @action(detail=False, methods=["get", "post"], url_path="instructor-requests")
    def solicitar_instructor(self, request):
        if request.method == "GET":
            return self._listar_solicitudes_instructor(request)

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

    def _listar_solicitudes_instructor(self, request):
        """`GET /users/instructor-requests/?estado=pendiente|aprobada|rechazada|todas` — solo Admin."""
        estado = request.query_params.get("estado", "pendiente")
        resultado = ListarSolicitudesInstructorQuery(
            SolicitudInstructorRepository(), UserRepository()
        ).execute(actor_rol=request.user.rol, estado=None if estado == "todas" else estado)
        return Response(
            [
                {
                    "id": str(item.id),
                    "estado": item.estado,
                    "orcid": item.orcid,
                    "orcid_url": f"https://orcid.org/{item.orcid}",
                    "tipo": item.tipo,
                    "institucion": item.institucion,
                    "especialidades": item.especialidades,
                    "motivacion": item.motivacion,
                    "nombre_declarado": item.nombre_declarado,
                    "usuario": {
                        "id": str(item.usuario_id),
                        "email": item.usuario_email,
                        "nombre_completo": item.usuario_nombre,
                        "registrado_desde": item.usuario_desde.isoformat() if item.usuario_desde else None,
                    },
                    "openalex": item.resultado_openalex,
                    "motivo_rechazo": item.motivo_rechazo,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None,
                }
                for item in resultado
            ],
            status=status.HTTP_200_OK,
        )

    def _resolver_solicitud(self, request, solicitud_pk: str, aprobar: bool):
        serializer = ResolverSolicitudInstructorRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resultado = ResolverSolicitudInstructorUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            solicitud_repository=SolicitudInstructorRepository(),
            user_repository=UserRepository(),
        ).execute(
            ResolverSolicitudInstructorDTO(
                solicitud_id=_parsear_uuid(solicitud_pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
                aprobar=aprobar,
                motivo=serializer.validated_data.get("motivo"),
            )
        )
        return Response(_serializar_solicitud_instructor(resultado), status=status.HTTP_200_OK)

    @action(
        detail=False, methods=["post"], url_path=r"instructor-requests/(?P<solicitud_pk>[^/.]+)/approve"
    )
    def aprobar_solicitud_instructor(self, request, solicitud_pk=None):
        return self._resolver_solicitud(request, solicitud_pk, aprobar=True)

    @action(
        detail=False, methods=["post"], url_path=r"instructor-requests/(?P<solicitud_pk>[^/.]+)/reject"
    )
    def rechazar_solicitud_instructor(self, request, solicitud_pk=None):
        return self._resolver_solicitud(request, solicitud_pk, aprobar=False)

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
