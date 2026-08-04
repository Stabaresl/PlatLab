import uuid

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from modules.notifications.application.dtos import ListarNotificacionesDTO, MarcarLeidaDTO
from modules.notifications.application.queries.listar_notificaciones import (
    ListarNotificacionesQuery,
)
from modules.notifications.application.use_cases.marcar_leida import MarcarLeidaUseCase
from modules.notifications.infrastructure.repositories import NotificacionRepository
from modules.notifications.presentation.serializers import ListarNotificacionesQuerySerializer
from modules.shared.domain.exceptions import NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.shared.presentation.pagination import ListaPagination

_ID_INVALIDO_MSG = "Notificación no encontrada."


def _parsear_uuid(valor: str) -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (ValueError, TypeError, AttributeError) as exc:
        raise NotFoundError(_ID_INVALIDO_MSG) from exc


def _serializar(resultado) -> dict:
    return {
        "id": str(resultado.id),
        "tipo": resultado.tipo,
        "mensaje": resultado.mensaje,
        "canal": resultado.canal,
        "leida": resultado.leida,
        "entidad_tipo": resultado.entidad_tipo,
        "entidad_id": str(resultado.entidad_id) if resultado.entidad_id else None,
        "fecha_creacion": resultado.fecha_creacion.isoformat(),
    }


class NotificationViewSet(ViewSet):
    """`/api/v1/notifications/` — HE-13, api.md §9."""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        query_serializer = ListarNotificacionesQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        resultado = ListarNotificacionesQuery(NotificacionRepository()).execute(
            ListarNotificacionesDTO(
                user_id=request.user.id,
                leida=query_serializer.validated_data.get("leida"),
            )
        )
        serializados = [_serializar(item) for item in resultado]
        paginator = ListaPagination()
        pagina = paginator.paginate_queryset(serializados, request, view=self)
        return paginator.get_paginated_response(pagina)

    @action(detail=True, methods=["patch"], url_path="read")
    def marcar_leida(self, request, pk=None):
        use_case = MarcarLeidaUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            notificacion_repository=NotificacionRepository(),
        )
        resultado = use_case.execute(
            MarcarLeidaDTO(notificacion_id=_parsear_uuid(pk), actor_id=request.user.id)
        )
        return Response(_serializar(resultado), status=status.HTTP_200_OK)
