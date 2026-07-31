import uuid

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from modules.laboratories.application.dtos import (
    AgregarPreguntaDTO,
    AprobarLaboratorioDTO,
    CambiarVisibilidadCatalogoDTO,
    CrearExamenDTO,
    CrearLaboratorioDTO,
    CrearSeccionDTO,
    DefinirFlagDTO,
    DuplicarLaboratorioDTO,
    EditarLaboratorioDTO,
    EditarSeccionDTO,
    ListarLaboratoriosFiltroDTO,
    ObtenerContenidoSeccionPreviewDTO,
    PublicarLaboratorioDTO,
    RechazarLaboratorioDTO,
    SolicitarRevisionLaboratorioDTO,
    SubirDockerfileDTO,
    VerificarFlagPreviewDTO,
)
from modules.laboratories.application.queries.listar_laboratorios import (
    ListarLaboratoriosQuery,
)
from modules.laboratories.application.queries.listar_laboratorios_en_revision import (
    ListarLaboratoriosEnRevisionQuery,
)
from modules.laboratories.application.queries.listar_laboratorios_personalizados_publicados import (
    ListarLaboratoriosPersonalizadosPublicadosQuery,
)
from modules.laboratories.application.queries.obtener_contenido_seccion_preview import (
    ObtenerContenidoSeccionPreviewQuery,
)
from modules.laboratories.application.queries.obtener_detalle_laboratorio import (
    ObtenerDetalleLaboratorioQuery,
)
from modules.laboratories.application.queries.obtener_toc import ObtenerTOCQuery
from modules.laboratories.application.queries.verificar_flag_preview import (
    VerificarFlagPreviewQuery,
)
from modules.laboratories.application.use_cases.agregar_pregunta import AgregarPreguntaUseCase
from modules.laboratories.application.use_cases.aprobar_laboratorio import (
    AprobarLaboratorioUseCase,
)
from modules.laboratories.application.use_cases.cambiar_visibilidad_catalogo import (
    CambiarVisibilidadCatalogoUseCase,
)
from modules.laboratories.application.use_cases.crear_examen import CrearExamenUseCase
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
from modules.laboratories.application.use_cases.rechazar_laboratorio import (
    RechazarLaboratorioUseCase,
)
from modules.laboratories.application.use_cases.solicitar_revision_laboratorio import (
    SolicitarRevisionLaboratorioUseCase,
)
from modules.laboratories.application.use_cases.subir_dockerfile_seccion import (
    SubirDockerfileSeccionUseCase,
)
from modules.laboratories.infrastructure.asignacion_inscripcion_provider import (
    AsignacionInscripcionProvider,
)
from modules.laboratories.infrastructure.cached_laboratorio_repository import (
    CachedLaboratorioRepository,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.laboratories.presentation.serializers import (
    AgregarPreguntaRequestSerializer,
    CambiarVisibilidadCatalogoRequestSerializer,
    CatalogoFiltroQuerySerializer,
    CrearLaboratorioRequestSerializer,
    CrearSeccionRequestSerializer,
    DefinirFlagRequestSerializer,
    EditarLaboratorioRequestSerializer,
    EditarSeccionRequestSerializer,
    PreviewFlagRequestSerializer,
    RechazarLaboratorioRequestSerializer,
    SubirDockerfileRequestSerializer,
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
        "visible_en_catalogo": resultado.visible_en_catalogo,
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


def _es_admin(request) -> bool:
    user = request.user
    return bool(getattr(user, "is_authenticated", False)) and user.rol == "administrador"


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

    def _inscripcion_provider(self):
        return AsignacionInscripcionProvider()

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

        resultados = ListarLaboratoriosQuery(
            self._repositorio(), self._inscripcion_provider()
        ).execute(filtro)
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
        instructor_id, estudiante_id = _resolver_ids(request)
        detalle = ObtenerDetalleLaboratorioQuery(
            self._repositorio(), self._inscripcion_provider()
        ).execute(
            laboratorio_id=_parsear_uuid(pk),
            instructor_id=instructor_id,
            estudiante_id=estudiante_id,
            es_admin=_es_admin(request),
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
                "motivo_rechazo": detalle.motivo_rechazo,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="toc")
    def toc(self, request, pk=None):
        instructor_id, estudiante_id = _resolver_ids(request)
        toc = ObtenerTOCQuery(self._repositorio(), self._inscripcion_provider()).execute(
            laboratorio_id=_parsear_uuid(pk),
            instructor_id=instructor_id,
            estudiante_id=estudiante_id,
            es_admin=_es_admin(request),
        )

        return Response(
            {
                "laboratorio_id": str(toc.laboratorio_id),
                "secciones": [
                    {
                        "id": str(s.id),
                        "orden": s.orden,
                        "titulo": s.titulo,
                        "tiene_practica": s.tiene_practica,
                        "duracion_estimada_minutos": s.duracion_estimada_minutos,
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
        self._repositorio().invalidar_catalogo()

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
        self._repositorio().invalidar_catalogo()

        return Response(_serializar_resultado_laboratorio(resultado), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="submit-review")
    def solicitar_revision(self, request, pk=None):
        use_case = SolicitarRevisionLaboratorioUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            laboratorio_repository=LaboratorioRepository(),
        )
        resultado = use_case.execute(
            SolicitarRevisionLaboratorioDTO(
                laboratorio_id=_parsear_uuid(pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
            )
        )
        return Response(_serializar_resultado_laboratorio(resultado), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="approve")
    def aprobar(self, request, pk=None):
        use_case = AprobarLaboratorioUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            laboratorio_repository=LaboratorioRepository(),
        )
        resultado = use_case.execute(
            AprobarLaboratorioDTO(
                laboratorio_id=_parsear_uuid(pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
            )
        )
        self._repositorio().invalidar_catalogo()
        return Response(_serializar_resultado_laboratorio(resultado), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="reject")
    def rechazar(self, request, pk=None):
        serializer = RechazarLaboratorioRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = RechazarLaboratorioUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            laboratorio_repository=LaboratorioRepository(),
        )
        resultado = use_case.execute(
            RechazarLaboratorioDTO(
                laboratorio_id=_parsear_uuid(pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
                **serializer.validated_data,
            )
        )
        self._repositorio().invalidar_catalogo()
        return Response(_serializar_resultado_laboratorio(resultado), status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"], url_path="catalog-visibility")
    def cambiar_visibilidad_catalogo(self, request, pk=None):
        serializer = CambiarVisibilidadCatalogoRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = CambiarVisibilidadCatalogoUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            laboratorio_repository=LaboratorioRepository(),
        )
        resultado = use_case.execute(
            CambiarVisibilidadCatalogoDTO(
                laboratorio_id=_parsear_uuid(pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
                **serializer.validated_data,
            )
        )
        self._repositorio().invalidar_catalogo()
        return Response(_serializar_resultado_laboratorio(resultado), status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="published-custom")
    def personalizados_publicados(self, request):
        resultados = ListarLaboratoriosPersonalizadosPublicadosQuery(
            LaboratorioRepository()
        ).execute(actor_rol=request.user.rol)
        return Response(
            [
                {
                    "id": str(item.id),
                    "nombre": item.nombre,
                    "instructor_id": str(item.instructor_id) if item.instructor_id else None,
                    "visible_en_catalogo": item.visible_en_catalogo,
                }
                for item in resultados
            ],
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="review-queue")
    def cola_revision(self, request):
        resultados = ListarLaboratoriosEnRevisionQuery(LaboratorioRepository()).execute(
            actor_rol=request.user.rol
        )
        return Response(
            [
                {
                    "id": str(item.id),
                    "nombre": item.nombre,
                    "instructor_id": str(item.instructor_id) if item.instructor_id else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                }
                for item in resultados
            ],
            status=status.HTTP_200_OK,
        )

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

    @action(detail=True, methods=["post"], url_path=r"sections/(?P<seccion_pk>[^/.]+)/dockerfile")
    def subir_dockerfile(self, request, pk=None, seccion_pk=None):
        serializer = SubirDockerfileRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        archivo = serializer.validated_data["archivo"]

        use_case = SubirDockerfileSeccionUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            laboratorio_repository=LaboratorioRepository(),
        )
        resultado = use_case.execute(
            SubirDockerfileDTO(
                laboratorio_id=_parsear_uuid(pk),
                seccion_id=_parsear_uuid(seccion_pk),
                archivo_nombre=archivo.name,
                archivo_contenido=archivo.read(),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
            )
        )
        return Response(
            {
                "id": str(resultado.id),
                "seccion_id": str(resultado.seccion_id),
                "archivo_url": resultado.archivo_url,
                "nombre_archivo": resultado.nombre_archivo,
                "tamano_kb": resultado.tamano_kb,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path=r"sections/(?P<seccion_pk>[^/.]+)/preview")
    def preview_seccion(self, request, pk=None, seccion_pk=None):
        resultado = ObtenerContenidoSeccionPreviewQuery(LaboratorioRepository()).execute(
            ObtenerContenidoSeccionPreviewDTO(
                laboratorio_id=_parsear_uuid(pk),
                seccion_id=_parsear_uuid(seccion_pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
            )
        )
        return Response(
            {
                "seccion_id": str(resultado.seccion_id),
                "titulo": resultado.titulo,
                "contenido_teorico": resultado.contenido_teorico,
                "tiene_practica": resultado.tiene_practica,
                "objetivos": resultado.objetivos,
                "duracion_estimada_minutos": resultado.duracion_estimada_minutos,
                "pasos_guia": resultado.pasos_guia,
                "entorno_practica": resultado.entorno_practica,
                "tiene_dockerfile": resultado.tiene_dockerfile,
                "dockerfile_url": resultado.dockerfile_url,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path=r"sections/(?P<seccion_pk>[^/.]+)/preview/check-flag",
    )
    def preview_check_flag(self, request, pk=None, seccion_pk=None):
        serializer = PreviewFlagRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        correcto = VerificarFlagPreviewQuery(LaboratorioRepository()).execute(
            VerificarFlagPreviewDTO(
                laboratorio_id=_parsear_uuid(pk),
                seccion_id=_parsear_uuid(seccion_pk),
                valor=serializer.validated_data["valor"],
                actor_id=request.user.id,
                actor_rol=request.user.rol,
            )
        )
        return Response({"correcto": correcto}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="exam")
    def crear_examen(self, request, pk=None):
        use_case = CrearExamenUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            laboratorio_repository=LaboratorioRepository(),
        )
        resultado = use_case.execute(
            CrearExamenDTO(
                laboratorio_id=_parsear_uuid(pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
            )
        )
        return Response(
            {"id": str(resultado.id), "laboratorio_id": str(resultado.laboratorio_id)},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="exam/questions")
    def agregar_pregunta(self, request, pk=None):
        serializer = AgregarPreguntaRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = AgregarPreguntaUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            laboratorio_repository=LaboratorioRepository(),
        )
        resultado = use_case.execute(
            AgregarPreguntaDTO(
                laboratorio_id=_parsear_uuid(pk),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
                **serializer.validated_data,
            )
        )
        return Response(
            {
                "id": str(resultado.id),
                "examen_id": str(resultado.examen_id),
                "enunciado": resultado.enunciado,
                "tipo": resultado.tipo,
                "opciones": resultado.opciones,
            },
            status=status.HTTP_201_CREATED,
        )
