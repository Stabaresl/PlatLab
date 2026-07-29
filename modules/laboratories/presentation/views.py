import uuid

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from modules.laboratories.application.dtos import (
    CrearLaboratorioDTO,
    CrearSeccionDTO,
    DefinirFlagDTO,
    DuplicarLaboratorioDTO,
    EditarLaboratorioDTO,
    EditarSeccionDTO,
    ListarLaboratoriosFiltroDTO,
    PublicarLaboratorioDTO,
)
from modules.laboratories.application.queries.listar_laboratorios import (
    ListarLaboratoriosQuery,
)
from modules.laboratories.application.queries.obtener_detalle_laboratorio import (
    ObtenerDetalleLaboratorioQuery,
)
from modules.laboratories.application.queries.obtener_toc import ObtenerTOCQuery
from modules.laboratories.application.use_cases.crear_laboratorio import (
    CrearLaboratorioUseCase,
)
from modules.laboratories.application.use_cases.crear_seccion import CrearSeccionUseCase
from modules.laboratories.application.use_cases.definir_flag import DefinirFlagUseCase
from modules.laboratories.application.use_cases.duplicar_laboratorio import (
    DuplicarLaboratorioUseCase,
)
from modules.laboratories.application.use_cases.editar_laboratorio import (
    EditarLaboratorioUseCase,
)
from modules.laboratories.application.use_cases.editar_seccion import EditarSeccionUseCase
from modules.laboratories.application.use_cases.publicar_laboratorio import (
    PublicarLaboratorioUseCase,
)
from modules.laboratories.infrastructure.cached_laboratorio_repository import (
    CachedLaboratorioRepository,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.laboratories.presentation.serializers import (
    CatalogoFiltroQuerySerializer,
    CrearLaboratorioRequestSerializer,
    CrearSeccionRequestSerializer,
    DefinirFlagRequestSerializer,
    EditarLaboratorioRequestSerializer,
    EditarSeccionRequestSerializer,
)
from modules.shared.domain.exceptions import NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork

_ID_INVALIDO_MSG = "Laboratorio no encontrado."


def _parsear_uuid(valor: str) -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (ValueError, TypeError, AttributeError) as exc:
        raise NotFoundError(_ID_INVALIDO_MSG) from exc


def _serializar_resultado_laboratorio(resultado) -> dict:
    return {
        "id": str(resultado.id),
        "nombre": resultado.nombre,
        "estado": resultado.estado,
        "tipo": resultado.tipo,
    }


def _serializar_resultado_seccion(resultado) -> dict:
    return {
        "id": str(resultado.id),
        "laboratorio_id": str(resultado.laboratorio_id),
        "orden": resultado.orden,
        "titulo": resultado.titulo,
        "tiene_practica": resultado.tiene_practica,
    }


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

    _ACCIONES_PUBLICAS = {"list", "retrieve", "toc"}

    def get_permissions(self):
        if self.action in self._ACCIONES_PUBLICAS:
            return [AllowAny()]
        return [IsAuthenticated()]

    def _repositorio(self):
        return CachedLaboratorioRepository(LaboratorioRepository())

    def list(self, request):
        query_serializer = CatalogoFiltroQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        instructor_id, estudiante_id = _resolver_ids(request)
        filtro = ListarLaboratoriosFiltroDTO(
            dificultad=query_serializer.validated_data.get("dificultad"),
            tema=query_serializer.validated_data.get("tema"),
            nombre=query_serializer.validated_data.get("nombre"),
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

    @action(detail=True, methods=["put"], url_path=r"sections/(?P<seccion_pk>[^/.]+)/flag")
    def definir_flag(self, request, pk=None, seccion_pk=None):
        serializer = DefinirFlagRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = DefinirFlagUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            laboratorio_repository=LaboratorioRepository(),
        )
        resultado = use_case.execute(
            DefinirFlagDTO(
                laboratorio_id=_parsear_uuid(pk),
                seccion_id=_parsear_uuid(seccion_pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
                **serializer.validated_data,
            )
        )

        return Response(
            {"id": str(resultado.id), "seccion_id": str(resultado.seccion_id)},
            status=status.HTTP_200_OK,
        )

    def create(self, request):
        serializer = CrearLaboratorioRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = CrearLaboratorioUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            laboratorio_repository=LaboratorioRepository(),
        )
        resultado = use_case.execute(
            CrearLaboratorioDTO(
                actor_id=request.user.id,
                actor_rol=request.user.rol,
                **serializer.validated_data,
            )
        )

        return Response(
            _serializar_resultado_laboratorio(resultado), status=status.HTTP_201_CREATED
        )

    def partial_update(self, request, pk=None):
        serializer = EditarLaboratorioRequestSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        use_case = EditarLaboratorioUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            laboratorio_repository=LaboratorioRepository(),
        )
        resultado = use_case.execute(
            EditarLaboratorioDTO(
                laboratorio_id=_parsear_uuid(pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
                **serializer.validated_data,
            )
        )

        return Response(_serializar_resultado_laboratorio(resultado), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="publish")
    def publicar(self, request, pk=None):
        use_case = PublicarLaboratorioUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            laboratorio_repository=LaboratorioRepository(),
        )
        resultado = use_case.execute(
            PublicarLaboratorioDTO(
                laboratorio_id=_parsear_uuid(pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
            )
        )

        return Response(_serializar_resultado_laboratorio(resultado), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="duplicate")
    def duplicar(self, request, pk=None):
        use_case = DuplicarLaboratorioUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            laboratorio_repository=LaboratorioRepository(),
        )
        resultado = use_case.execute(
            DuplicarLaboratorioDTO(
                laboratorio_id=_parsear_uuid(pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
            )
        )

        return Response(
            _serializar_resultado_laboratorio(resultado), status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"], url_path="sections")
    def crear_seccion(self, request, pk=None):
        serializer = CrearSeccionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = CrearSeccionUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            laboratorio_repository=LaboratorioRepository(),
        )
        resultado = use_case.execute(
            CrearSeccionDTO(
                laboratorio_id=_parsear_uuid(pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
                **serializer.validated_data,
            )
        )

        return Response(_serializar_resultado_seccion(resultado), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path=r"sections/(?P<seccion_pk>[^/.]+)")
    def editar_seccion(self, request, pk=None, seccion_pk=None):
        serializer = EditarSeccionRequestSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        use_case = EditarSeccionUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            laboratorio_repository=LaboratorioRepository(),
        )
        resultado = use_case.execute(
            EditarSeccionDTO(
                laboratorio_id=_parsear_uuid(pk),
                seccion_id=_parsear_uuid(seccion_pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
                **serializer.validated_data,
            )
        )

        return Response(_serializar_resultado_seccion(resultado), status=status.HTTP_200_OK)
