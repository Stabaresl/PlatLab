import uuid

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from modules.laboratories.application.dtos import ListarLaboratoriosFiltroDTO
from modules.laboratories.application.queries.listar_laboratorios import (
    ListarLaboratoriosQuery,
)
from modules.laboratories.application.queries.obtener_detalle_laboratorio import (
    ObtenerDetalleLaboratorioQuery,
)
from modules.laboratories.application.queries.obtener_toc import ObtenerTOCQuery
from modules.laboratories.infrastructure.cached_laboratorio_repository import (
    CachedLaboratorioRepository,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.laboratories.presentation.serializers import CatalogoFiltroQuerySerializer
from modules.shared.domain.exceptions import NotFoundError

_ID_INVALIDO_MSG = "Laboratorio no encontrado."


def _parsear_uuid(valor: str) -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (ValueError, TypeError, AttributeError) as exc:
        raise NotFoundError(_ID_INVALIDO_MSG) from exc


def _resolver_ids(request) -> tuple[uuid.UUID | None, uuid.UUID | None]:
    """
    Resuelve `instructor_id`/`estudiante_id` desde `request.user` (JWT ya
    validado por `JWTAuthentication`) — nunca desde un query param, para
    que un visitante no pueda simular ser instructor cambiando la URL
    (HI-01/HE-02). Un visitante anónimo o un Administrador no activan
    ninguna de las dos ramas (ven el catálogo público, igual que HV-02).
    """
    user = request.user
    if not getattr(user, "is_authenticated", False):
        return None, None
    if user.rol == "instructor":
        return user.id, None
    if user.rol == "estudiante":
        return None, user.id
    return None, None


class CatalogoPagination(LimitOffsetPagination):
    """
    `ListarLaboratoriosQuery` ya devuelve una lista materializada de DTOs
    (Application no expone el queryset del ORM a Presentation, backend.md
    §2) — `CursorPagination` de DRF necesita un queryset real (llama
    `.order_by()` sobre él), por lo que no aplica aquí. `LimitOffsetPagination`
    sí funciona sobre listas ya ordenadas (el orden por `nombre` ya lo
    aplica `LaboratorioRepository.find_catalogo` a nivel de query).
    """

    default_limit = 20


class LaboratorioViewSet(ViewSet):
    """
    `/api/v1/laboratories/` — HV-02/HE-02 (catálogo), HV-03 (detalle/TOC),
    HI-01 (catálogo del instructor). Público por defecto; el rol del
    usuario autenticado (si lo hay) amplía la visibilidad o agrega
    `inscrito`, nunca la reduce (api.md §5).
    """

    permission_classes = [AllowAny]

    def _repositorio(self):
        return CachedLaboratorioRepository(LaboratorioRepository())

    def list(self, request):
        query_serializer = CatalogoFiltroQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        instructor_id, estudiante_id = _resolver_ids(request)
        filtro = ListarLaboratoriosFiltroDTO(
            dificultad=query_serializer.validated_data.get("dificultad"),
            tema=query_serializer.validated_data.get("tema"),
            instructor_id=instructor_id,
            estudiante_id=estudiante_id,
        )

        resultados = ListarLaboratoriosQuery(self._repositorio()).execute(filtro)
        serializados = [
            {
                "id": str(item.id),
                "nombre": item.nombre,
                "descripcion": item.descripcion,
                "nivel_dificultad": item.nivel_dificultad,
                "estado": item.estado,
                "temas": item.temas,
                "inscrito": item.inscrito,
            }
            for item in resultados
        ]

        paginator = CatalogoPagination()
        pagina = paginator.paginate_queryset(serializados, request, view=self)
        return paginator.get_paginated_response(pagina)

    def retrieve(self, request, pk=None):
        instructor_id, _ = _resolver_ids(request)
        detalle = ObtenerDetalleLaboratorioQuery(self._repositorio()).execute(
            laboratorio_id=_parsear_uuid(pk), instructor_id=instructor_id
        )

        return Response(
            {
                "id": str(detalle.id),
                "nombre": detalle.nombre,
                "descripcion": detalle.descripcion,
                "nivel_dificultad": detalle.nivel_dificultad,
                "estado": detalle.estado,
                "temas": detalle.temas,
                "total_secciones": detalle.total_secciones,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="toc")
    def toc(self, request, pk=None):
        instructor_id, _ = _resolver_ids(request)
        toc = ObtenerTOCQuery(self._repositorio()).execute(
            laboratorio_id=_parsear_uuid(pk), instructor_id=instructor_id
        )

        return Response(
            {
                "laboratorio_id": str(toc.laboratorio_id),
                "secciones": [
                    {
                        "orden": s.orden,
                        "titulo": s.titulo,
                        "tiene_practica": s.tiene_practica,
                    }
                    for s in toc.secciones
                ],
            },
            status=status.HTTP_200_OK,
        )
