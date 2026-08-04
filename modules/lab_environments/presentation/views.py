import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.lab_environments.application.dtos import (
    DetenerEntornoDTO,
    IniciarEntornoDTO,
    ObtenerEstadoEntornoDTO,
)
from modules.lab_environments.application.queries.obtener_estado_entorno import (
    ObtenerEstadoEntornoQuery,
)
from modules.lab_environments.application.use_cases.detener_entorno import DetenerEntornoUseCase
from modules.lab_environments.application.use_cases.iniciar_entorno import IniciarEntornoUseCase
from modules.lab_environments.infrastructure.docker_provider import DockerContenedorProvider
from modules.lab_environments.infrastructure.repositories import EntornoRepository
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.domain.exceptions import NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork

_ID_INVALIDO_MSG = "Recurso no encontrado."


def _parsear_uuid(valor: str) -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (ValueError, TypeError, AttributeError) as exc:
        raise NotFoundError(_ID_INVALIDO_MSG) from exc


def _serializar_entorno(entorno) -> dict:
    return {
        "id": str(entorno.id),
        "estado": entorno.estado.value,
        "idle_timeout_minutos": settings.LAB_ENV_IDLE_MINUTES,
        "max_lifetime_minutos": settings.LAB_ENV_MAX_LIFETIME_MINUTES,
    }


class EntornoStartView(APIView):
    """
    `POST /lab-environments/{assignment_id}/sections/{section_id}/start/`
    — inicia (o reconecta a) el entorno de práctica real de la sección.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, assignment_id, section_id):
        resultado = IniciarEntornoUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            entorno_repository=EntornoRepository(),
            progreso_repository=ProgresoRepository(),
            laboratorio_repository=LaboratorioRepository(),
            max_concurrentes=settings.LAB_ENV_MAX_CONCURRENTES,
            idle_timeout_minutos=settings.LAB_ENV_IDLE_MINUTES,
            max_lifetime_minutos=settings.LAB_ENV_MAX_LIFETIME_MINUTES,
        ).execute(
            IniciarEntornoDTO(
                asignacion_id=_parsear_uuid(assignment_id),
                seccion_id=_parsear_uuid(section_id),
                estudiante_id=request.user.id,
            )
        )

        return Response(
            {
                "id": str(resultado.id),
                "estado": resultado.estado,
                "idle_timeout_minutos": resultado.idle_timeout_minutos,
                "max_lifetime_minutos": resultado.max_lifetime_minutos,
            },
            status=status.HTTP_200_OK,
        )


class EntornoStopView(APIView):
    """`POST /lab-environments/{entorno_id}/stop/` — apagado explícito por el estudiante."""

    permission_classes = [IsAuthenticated]

    def post(self, request, entorno_id):
        DetenerEntornoUseCase(
            unit_of_work=BaseUnitOfWork(),
            entorno_repository=EntornoRepository(),
            contenedor_provider=DockerContenedorProvider(),
        ).execute(
            DetenerEntornoDTO(entorno_id=_parsear_uuid(entorno_id), estudiante_id=request.user.id)
        )
        return Response({"detenido": True}, status=status.HTTP_200_OK)


class EntornoStatusView(APIView):
    """`GET /lab-environments/{assignment_id}/sections/{section_id}/status/`."""

    permission_classes = [IsAuthenticated]

    def get(self, request, assignment_id, section_id):
        entorno = ObtenerEstadoEntornoQuery(
            entorno_repository=EntornoRepository(),
            progreso_repository=ProgresoRepository(),
        ).execute(
            ObtenerEstadoEntornoDTO(
                asignacion_id=_parsear_uuid(assignment_id),
                seccion_id=_parsear_uuid(section_id),
                estudiante_id=request.user.id,
            )
        )

        if entorno is None:
            return Response({"activo": False}, status=status.HTTP_200_OK)

        data = _serializar_entorno(entorno)
        data["activo"] = True
        return Response(data, status=status.HTTP_200_OK)
