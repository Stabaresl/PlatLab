import uuid

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from modules.reports.application.dtos import (
    CambiarEstadoReporteDTO,
    CrearReporteDTO,
    ListarReportesDTO,
    ListarReportesPropiosDTO,
)
from modules.reports.application.queries.listar_reportes import ListarReportesQuery
from modules.reports.application.queries.listar_reportes_propios import (
    ListarReportesPropiosQuery,
)
from modules.reports.application.use_cases.cambiar_estado_reporte import (
    CambiarEstadoReporteUseCase,
)
from modules.reports.application.use_cases.crear_reporte import CrearReporteUseCase
from modules.reports.infrastructure.repositories import ReporteRepository
from modules.reports.presentation.serializers import (
    CambiarEstadoReporteRequestSerializer,
    CrearReporteRequestSerializer,
    ListarReportesQuerySerializer,
)
from modules.shared.domain.exceptions import NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork

_ID_INVALIDO_MSG = "Reporte no encontrado."


def _parsear_uuid(valor: str) -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (ValueError, TypeError, AttributeError) as exc:
        raise NotFoundError(_ID_INVALIDO_MSG) from exc


def _serializar_reporte(resultado) -> dict:
    return {
        "id": str(resultado.id),
        "laboratorio_id": str(resultado.laboratorio_id),
        "estado": resultado.estado,
        "fecha_creacion": resultado.fecha_creacion.isoformat(),
    }


def _serializar_item(item) -> dict:
    return {
        "id": str(item.id),
        "laboratorio_id": str(item.laboratorio_id),
        "estado": item.estado,
        "descripcion": item.descripcion,
        "fecha_creacion": item.fecha_creacion.isoformat(),
        "fecha_resolucion": item.fecha_resolucion.isoformat() if item.fecha_resolucion else None,
    }


class ReportViewSet(ViewSet):
    """`/api/v1/reports/` — HE-12/HA-05, api.md §8."""

    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = CrearReporteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        adjunto = datos.get("adjunto")

        use_case = CrearReporteUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            reporte_repository=ReporteRepository(),
        )
        resultado = use_case.execute(
            CrearReporteDTO(
                estudiante_id=request.user.id,
                actor_rol=request.user.rol,
                laboratorio_id=datos["laboratorio_id"],
                descripcion=datos["descripcion"],
                seccion_id=datos.get("seccion_id"),
                archivo_nombre=adjunto.name if adjunto else None,
                archivo_contenido=adjunto.read() if adjunto else None,
            )
        )

        return Response(_serializar_reporte(resultado), status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="me")
    def mis_reportes(self, request):
        resultado = ListarReportesPropiosQuery(ReporteRepository()).execute(
            ListarReportesPropiosDTO(estudiante_id=request.user.id)
        )
        return Response(
            [_serializar_item(item) for item in resultado], status=status.HTTP_200_OK
        )

    def list(self, request):
        query_serializer = ListarReportesQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        datos = query_serializer.validated_data

        resultado = ListarReportesQuery(ReporteRepository()).execute(
            ListarReportesDTO(
                actor_rol=request.user.rol,
                estado=datos.get("estado"),
                laboratorio_id=datos.get("laboratorio"),
            )
        )
        return Response(
            [_serializar_item(item) for item in resultado], status=status.HTTP_200_OK
        )

    def partial_update(self, request, pk=None):
        serializer = CambiarEstadoReporteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = CambiarEstadoReporteUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            reporte_repository=ReporteRepository(),
        )
        resultado = use_case.execute(
            CambiarEstadoReporteDTO(
                reporte_id=_parsear_uuid(pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
                nuevo_estado=serializer.validated_data["estado"],
            )
        )
        return Response(_serializar_reporte(resultado), status=status.HTTP_200_OK)
