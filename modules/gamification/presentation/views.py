import uuid

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from modules.gamification.application.dtos import (
    CambiarAvatarDTO,
    EquiparCosmeticoDTO,
    EquiparTituloDTO,
    QuitarCosmeticoDTO,
    QuitarTituloDTO,
    SubirAvatarDTO,
)
from modules.gamification.application.queries.listar_catalogo import ListarCatalogoQuery
from modules.gamification.application.queries.obtener_perfil import ObtenerPerfilQuery
from modules.gamification.application.use_cases.cambiar_avatar import CambiarAvatarUseCase
from modules.gamification.application.use_cases.equipar_cosmetico import EquiparCosmeticoUseCase
from modules.gamification.application.use_cases.equipar_titulo import EquiparTituloUseCase
from modules.gamification.application.use_cases.quitar_cosmetico import QuitarCosmeticoUseCase
from modules.gamification.application.use_cases.quitar_titulo import QuitarTituloUseCase
from modules.gamification.application.use_cases.subir_avatar import SubirAvatarUseCase
from modules.gamification.domain.entities import AVATAR_PRESETS
from modules.gamification.infrastructure.avatar_storage import verificar_tamano_declarado
from modules.gamification.infrastructure.repositories import (
    CosmeticoDesbloqueadoRepository,
    CosmeticoRepository,
    LogroDesbloqueadoRepository,
    LogroRepository,
    PerfilJugadorRepository,
    TituloDesbloqueadoRepository,
    TituloRepository,
    XpOtorgadoRepository,
)
from modules.gamification.presentation.serializers import (
    CambiarAvatarRequestSerializer,
    EquiparCosmeticoRequestSerializer,
    EquiparTituloRequestSerializer,
    SubirAvatarRequestSerializer,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.roadmap.infrastructure.repositories import NodoRoadmapRepository
from modules.shared.domain.exceptions import NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork

_ID_INVALIDO_MSG = "Recurso no encontrado."


def _parsear_uuid(valor: str) -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (ValueError, TypeError, AttributeError) as exc:
        raise NotFoundError(_ID_INVALIDO_MSG) from exc


def _serializar_perfil(perfil) -> dict:
    return {
        "estudiante_id": str(perfil.estudiante_id),
        "xp": perfil.xp,
        "nivel": perfil.nivel,
        "xp_para_siguiente_nivel": perfil.xp_para_siguiente_nivel,
        "avatar_tipo": perfil.avatar_tipo,
        "avatar_valor": perfil.avatar_valor,
        "logros": [
            {
                "id": str(l.id),
                "clave": l.clave,
                "nombre": l.nombre,
                "descripcion": l.descripcion,
                "rareza": l.rareza,
                "desbloqueado": l.desbloqueado,
                "progreso": l.progreso,
            }
            for l in perfil.logros
        ],
        "cosmeticos": [
            {
                "id": str(c.id),
                "cosmetico_id": str(c.cosmetico_id),
                "clave": c.clave,
                "nombre": c.nombre,
                "tipo": c.tipo,
                "rareza": c.rareza,
                "color": c.color,
                "equipado": c.equipado,
            }
            for c in perfil.cosmeticos
        ],
        "titulos": [
            {
                "id": str(t.id),
                "titulo_id": str(t.titulo_id),
                "clave": t.clave,
                "nombre": t.nombre,
                "descripcion": t.descripcion,
                "rareza": t.rareza,
                "equipado": t.equipado,
            }
            for t in perfil.titulos
        ],
    }


def _repos_perfil():
    return dict(
        perfil_repository=PerfilJugadorRepository(),
        xp_otorgado_repository=XpOtorgadoRepository(),
        logro_repository=LogroRepository(),
        logro_desbloqueado_repository=LogroDesbloqueadoRepository(),
        cosmetico_repository=CosmeticoRepository(),
        cosmetico_desbloqueado_repository=CosmeticoDesbloqueadoRepository(),
        titulo_repository=TituloRepository(),
        titulo_desbloqueado_repository=TituloDesbloqueadoRepository(),
        nodo_roadmap_repository=NodoRoadmapRepository(),
    )


class GamificationViewSet(ViewSet):
    """
    `/api/v1/gamification/` — perfil propio, catálogo y avatar. Equipar/
    quitar cosméticos y títulos viven en sus propios ViewSets
    (`CosmeticoDesbloqueadoViewSet`/`TituloDesbloqueadoViewSet`).
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        resultado = ObtenerPerfilQuery(**_repos_perfil()).execute(
            estudiante_id=request.user.id, actor_rol=request.user.rol
        )
        return Response(_serializar_perfil(resultado), status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="catalogo")
    def catalogo(self, request):
        logros, cosmeticos, titulos = ListarCatalogoQuery(
            logro_repository=LogroRepository(),
            cosmetico_repository=CosmeticoRepository(),
            titulo_repository=TituloRepository(),
        ).execute()
        return Response(
            {
                "logros": [
                    {
                        "id": str(l.id),
                        "clave": l.clave,
                        "nombre": l.nombre,
                        "descripcion": l.descripcion,
                        "rareza": l.rareza,
                    }
                    for l in logros
                ],
                "cosmeticos": [
                    {
                        "id": str(c.id),
                        "clave": c.clave,
                        "nombre": c.nombre,
                        "tipo": c.tipo,
                        "rareza": c.rareza,
                        "color": c.color,
                        "logro_requerido_id": str(c.logro_requerido_id),
                    }
                    for c in cosmeticos
                ],
                "titulos": [
                    {
                        "id": str(t.id),
                        "clave": t.clave,
                        "nombre": t.nombre,
                        "descripcion": t.descripcion,
                        "rareza": t.rareza,
                        "logro_requerido_id": str(t.logro_requerido_id),
                    }
                    for t in titulos
                ],
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="avatar-presets")
    def avatar_presets(self, request):
        return Response(
            [
                {"clave": p.clave, "nombre": p.nombre, "emoji": p.emoji, "color": p.color}
                for p in AVATAR_PRESETS
            ],
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["patch"], url_path="avatar")
    def avatar(self, request):
        serializer = CambiarAvatarRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = CambiarAvatarUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            perfil_repository=PerfilJugadorRepository(),
        )
        resultado = use_case.execute(
            CambiarAvatarDTO(
                preset_clave=serializer.validated_data["clave"],
                actor_id=request.user.id,
                actor_rol=request.user.rol,
            )
        )
        return Response(
            {"avatar_tipo": resultado.avatar_tipo, "avatar_valor": resultado.avatar_valor},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="avatar/upload")
    def avatar_upload(self, request):
        serializer = SubirAvatarRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        archivo = serializer.validated_data["archivo"]
        verificar_tamano_declarado(archivo.size)

        use_case = SubirAvatarUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            perfil_repository=PerfilJugadorRepository(),
        )
        resultado = use_case.execute(
            SubirAvatarDTO(
                archivo_nombre=archivo.name,
                archivo_contenido=archivo.read(),
                actor_id=request.user.id,
                actor_rol=request.user.rol,
            )
        )
        return Response(
            {"avatar_tipo": resultado.avatar_tipo, "avatar_valor": resultado.avatar_valor},
            status=status.HTTP_200_OK,
        )


class CosmeticoDesbloqueadoViewSet(ViewSet):
    """`/api/v1/gamification/cosmeticos/` — equipar/quitar un cosmético ya desbloqueado."""

    permission_classes = [IsAuthenticated]

    def partial_update(self, request, pk=None):
        serializer = EquiparCosmeticoRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cosmetico_desbloqueado_id = _parsear_uuid(pk)

        if serializer.validated_data["equipado"]:
            use_case = EquiparCosmeticoUseCase(
                unit_of_work=BaseUnitOfWork(),
                event_dispatcher=EventDispatcher(),
                cosmetico_desbloqueado_repository=CosmeticoDesbloqueadoRepository(),
                cosmetico_repository=CosmeticoRepository(),
            )
            resultado = use_case.execute(
                EquiparCosmeticoDTO(
                    cosmetico_desbloqueado_id=cosmetico_desbloqueado_id,
                    actor_id=request.user.id,
                    actor_rol=request.user.rol,
                )
            )
        else:
            use_case = QuitarCosmeticoUseCase(
                unit_of_work=BaseUnitOfWork(),
                event_dispatcher=EventDispatcher(),
                cosmetico_desbloqueado_repository=CosmeticoDesbloqueadoRepository(),
            )
            resultado = use_case.execute(
                QuitarCosmeticoDTO(
                    cosmetico_desbloqueado_id=cosmetico_desbloqueado_id,
                    actor_id=request.user.id,
                    actor_rol=request.user.rol,
                )
            )

        return Response(
            {"id": str(resultado.id), "cosmetico_id": str(resultado.cosmetico_id), "equipado": resultado.equipado},
            status=status.HTTP_200_OK,
        )


class TituloDesbloqueadoViewSet(ViewSet):
    """`/api/v1/gamification/titulos/` — equipar/quitar un título ya desbloqueado."""

    permission_classes = [IsAuthenticated]

    def partial_update(self, request, pk=None):
        serializer = EquiparTituloRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        titulo_desbloqueado_id = _parsear_uuid(pk)

        if serializer.validated_data["equipado"]:
            use_case = EquiparTituloUseCase(
                unit_of_work=BaseUnitOfWork(),
                event_dispatcher=EventDispatcher(),
                titulo_desbloqueado_repository=TituloDesbloqueadoRepository(),
            )
            resultado = use_case.execute(
                EquiparTituloDTO(
                    titulo_desbloqueado_id=titulo_desbloqueado_id,
                    actor_id=request.user.id,
                    actor_rol=request.user.rol,
                )
            )
        else:
            use_case = QuitarTituloUseCase(
                unit_of_work=BaseUnitOfWork(),
                event_dispatcher=EventDispatcher(),
                titulo_desbloqueado_repository=TituloDesbloqueadoRepository(),
            )
            resultado = use_case.execute(
                QuitarTituloDTO(
                    titulo_desbloqueado_id=titulo_desbloqueado_id,
                    actor_id=request.user.id,
                    actor_rol=request.user.rol,
                )
            )

        return Response(
            {"id": str(resultado.id), "titulo_id": str(resultado.titulo_id), "equipado": resultado.equipado},
            status=status.HTTP_200_OK,
        )
