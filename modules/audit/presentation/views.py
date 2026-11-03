from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ViewSet

from modules.audit.application.dtos import ConsultarAuditoriaDTO
from modules.audit.application.queries.consultar_auditoria import ConsultarAuditoriaQuery
from modules.audit.infrastructure.repositories import AuditoriaRepository
from modules.audit.presentation.serializers import ConsultarAuditoriaQuerySerializer
from modules.shared.presentation.pagination import parametros_pagina, respuesta_paginada


def _serializar(item) -> dict:
    return {
        "id": str(item.id),
        "actor_id": str(item.actor_id) if item.actor_id else None,
        "accion": item.accion,
        "entidad_tipo": item.entidad_tipo,
        "entidad_id": str(item.entidad_id) if item.entidad_id else None,
        "timestamp": item.timestamp.isoformat(),
        "metadata": item.metadata,
    }


class AuditViewSet(ViewSet):
    """`/api/v1/audit/` — UC-12, api.md §10. Solo lectura; solo Admin (validado en Application)."""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        query_serializer = ConsultarAuditoriaQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        datos = query_serializer.validated_data

        limit, offset = parametros_pagina(request)
        resultado, total = ConsultarAuditoriaQuery(AuditoriaRepository()).execute_paginado(
            ConsultarAuditoriaDTO(
                actor_rol=request.user.rol,
                actor_id=datos.get("actor"),
                accion=datos.get("accion"),
                desde=datos.get("desde"),
                hasta=datos.get("hasta"),
            ),
            limit=limit,
            offset=offset,
        )
        return respuesta_paginada(
            request, [_serializar(item) for item in resultado], total, limit, offset
        )
