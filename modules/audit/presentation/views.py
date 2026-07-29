from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from modules.audit.application.dtos import ConsultarAuditoriaDTO
from modules.audit.application.queries.consultar_auditoria import ConsultarAuditoriaQuery
from modules.audit.infrastructure.repositories import AuditoriaRepository
from modules.audit.presentation.serializers import ConsultarAuditoriaQuerySerializer


def _serializar(item) -> dict:
    return {
        "id": str(item.id),
        "actor_id": str(item.actor_id) if item.actor_id else None,
        "accion": item.accion,
        "entidad_tipo": item.entidad_tipo,
        "entidad_id": str(item.entidad_id) if item.entidad_id else None,
        "timestamp": item.timestamp.isoformat(),
    }


class AuditViewSet(ViewSet):
    """`/api/v1/audit/` — UC-12, api.md §10. Solo lectura; solo Admin (validado en Application)."""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        query_serializer = ConsultarAuditoriaQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        datos = query_serializer.validated_data

        resultado = ConsultarAuditoriaQuery(AuditoriaRepository()).execute(
            ConsultarAuditoriaDTO(
                actor_rol=request.user.rol,
                actor_id=datos.get("actor"),
                accion=datos.get("accion"),
                desde=datos.get("desde"),
                hasta=datos.get("hasta"),
            )
        )
        return Response([_serializar(item) for item in resultado], status=status.HTTP_200_OK)
