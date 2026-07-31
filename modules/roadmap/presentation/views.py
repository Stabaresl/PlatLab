import uuid

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.roadmap.application.dtos import (
    AgregarNodoDTO,
    CrearCategoriaDTO,
    InscribirseRoadmapDTO,
    QuitarNodoDTO,
    ReordenarNodoDTO,
)
from modules.roadmap.application.queries.listar_categorias import ListarCategoriasQuery
from modules.roadmap.application.queries.listar_laboratorios_sin_roadmap import (
    ListarLaboratoriosSinRoadmapQuery,
)
from modules.roadmap.application.queries.listar_roadmap import ListarRoadmapQuery
from modules.roadmap.application.use_cases.agregar_nodo import AgregarNodoUseCase
from modules.roadmap.application.use_cases.crear_categoria import CrearCategoriaUseCase
from modules.roadmap.application.use_cases.inscribirse_roadmap import InscribirseRoadmapUseCase
from modules.roadmap.application.use_cases.quitar_nodo import QuitarNodoUseCase
from modules.roadmap.application.use_cases.reordenar_nodo import ReordenarNodoUseCase
from modules.roadmap.infrastructure.repositories import (
    CategoriaRoadmapRepository,
    NodoRoadmapRepository,
)
from modules.roadmap.presentation.serializers import (
    AgregarNodoRequestSerializer,
    CrearCategoriaRequestSerializer,
    ReordenarNodoRequestSerializer,
)
from modules.shared.domain.exceptions import NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork

_ID_INVALIDO_MSG = "Nodo de roadmap no encontrado."


def _parsear_uuid(valor: str) -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (ValueError, TypeError, AttributeError) as exc:
        raise NotFoundError(_ID_INVALIDO_MSG) from exc


def _estudiante_id_actual(request) -> uuid.UUID | None:
    user = request.user
    if getattr(user, "is_authenticated", False) and user.rol == "estudiante":
        return user.id
    return None


def _serializar_categoria(resultado) -> dict:
    return {"id": str(resultado.id), "nombre": resultado.nombre, "orden": resultado.orden}


def _serializar_nodo(resultado) -> dict:
    return {
        "id": str(resultado.id),
        "categoria_id": str(resultado.categoria_id),
        "laboratorio_id": str(resultado.laboratorio_id),
        "posicion": resultado.posicion,
    }


class RoadmapViewSet(ViewSet):
    """
    `/api/v1/roadmap/` — árbol público del roadmap (HV) + gestión de
    categorías y pool "sin asignar" (admin). El CRUD de nodos vive en
    `NodoRoadmapViewSet` (`/api/v1/roadmap/nodos/`) — tiene su propia
    forma REST natural (create/partial_update/destroy) que no encaja
    como sub-recurso de una categoría puntual.
    """

    permission_classes = [AllowAny]
    _ACCIONES_PUBLICAS = {"list"}

    def get_permissions(self):
        if self.action in self._ACCIONES_PUBLICAS:
            return [AllowAny()]
        return [IsAuthenticated()]

    def list(self, request):
        resultado = ListarRoadmapQuery(
            categoria_repository=CategoriaRoadmapRepository(),
            nodo_repository=NodoRoadmapRepository(),
            laboratorio_repository=LaboratorioRepository(),
            asignacion_repository=AsignacionRepository(),
            progreso_repository=ProgresoRepository(),
        ).execute(estudiante_id=_estudiante_id_actual(request))

        return Response(
            [
                {
                    "id": str(categoria.id),
                    "nombre": categoria.nombre,
                    "orden": categoria.orden,
                    "nodos": [
                        {
                            "id": str(nodo.id),
                            "laboratorio_id": str(nodo.laboratorio_id),
                            "posicion": nodo.posicion,
                            "nombre": nodo.nombre,
                            "nivel_dificultad": nodo.nivel_dificultad,
                            "temas": nodo.temas,
                            "prerequisitos": [
                                {"laboratorio_id": str(p.laboratorio_id), "nombre": p.nombre}
                                for p in nodo.prerequisitos
                            ],
                            "estado": nodo.estado,
                        }
                        for nodo in categoria.nodos
                    ],
                }
                for categoria in resultado
            ],
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get", "post"], url_path="categorias")
    def categorias(self, request):
        if request.method == "GET":
            resultado = ListarCategoriasQuery(CategoriaRoadmapRepository()).execute(
                actor_rol=request.user.rol
            )
            return Response(
                [_serializar_categoria(item) for item in resultado], status=status.HTTP_200_OK
            )

        serializer = CrearCategoriaRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = CrearCategoriaUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            categoria_repository=CategoriaRoadmapRepository(),
        )
        resultado = use_case.execute(
            CrearCategoriaDTO(
                nombre=serializer.validated_data["nombre"],
                actor_id=request.user.id,
                actor_rol=request.user.rol,
            )
        )
        return Response(_serializar_categoria(resultado), status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="sin-asignar")
    def sin_asignar(self, request):
        resultado = ListarLaboratoriosSinRoadmapQuery(
            laboratorio_repository=LaboratorioRepository(),
            nodo_repository=NodoRoadmapRepository(),
        ).execute(actor_rol=request.user.rol)
        return Response(
            [
                {
                    "id": str(item.id),
                    "nombre": item.nombre,
                    "nivel_dificultad": item.nivel_dificultad,
                    "temas": item.temas,
                }
                for item in resultado
            ],
            status=status.HTTP_200_OK,
        )


class NodoRoadmapViewSet(ViewSet):
    """`/api/v1/roadmap/nodos/` — CRUD de nodos (admin) + inscripción (estudiante)."""

    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = AgregarNodoRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        posicion = datos.get("posicion")
        if posicion is None:
            posicion = len(NodoRoadmapRepository().find_por_categoria(datos["categoria_id"]))

        use_case = AgregarNodoUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            categoria_repository=CategoriaRoadmapRepository(),
            nodo_repository=NodoRoadmapRepository(),
            laboratorio_repository=LaboratorioRepository(),
        )
        resultado = use_case.execute(
            AgregarNodoDTO(
                categoria_id=datos["categoria_id"],
                laboratorio_id=datos["laboratorio_id"],
                posicion=posicion,
                actor_id=request.user.id,
                actor_rol=request.user.rol,
            )
        )
        return Response(_serializar_nodo(resultado), status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        serializer = ReordenarNodoRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        use_case = ReordenarNodoUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            categoria_repository=CategoriaRoadmapRepository(),
            nodo_repository=NodoRoadmapRepository(),
        )
        resultado = use_case.execute(
            ReordenarNodoDTO(
                nodo_id=_parsear_uuid(pk),
                categoria_id=datos["categoria_id"],
                posicion=datos["posicion"],
                actor_id=request.user.id,
                actor_rol=request.user.rol,
            )
        )
        return Response(_serializar_nodo(resultado), status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        use_case = QuitarNodoUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            nodo_repository=NodoRoadmapRepository(),
        )
        use_case.execute(
            QuitarNodoDTO(
                nodo_id=_parsear_uuid(pk), actor_id=request.user.id, actor_rol=request.user.rol
            )
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="inscribirse")
    def inscribirse(self, request, pk=None):
        use_case = InscribirseRoadmapUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            nodo_repository=NodoRoadmapRepository(),
            asignacion_repository=AsignacionRepository(),
            laboratorio_repository=LaboratorioRepository(),
            progreso_repository=ProgresoRepository(),
        )
        resultado = use_case.execute(
            InscribirseRoadmapDTO(
                nodo_id=_parsear_uuid(pk), actor_id=request.user.id, actor_rol=request.user.rol
            )
        )
        return Response(
            {
                "id": str(resultado.id),
                "laboratorio_id": str(resultado.laboratorio_id),
                "estado": resultado.estado,
            },
            status=status.HTTP_201_CREATED,
        )
