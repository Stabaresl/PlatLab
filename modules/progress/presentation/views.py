import uuid

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.application.dtos import (
    CompletarSeccionTeoricaDTO,
    EnviarExamenDTO,
    IniciarExamenDTO,
    ObtenerContenidoSeccionDTO,
    ObtenerExamenDTO,
    ObtenerHistorialDTO,
    ObtenerPistaDTO,
    ObtenerProgresoDTO,
    ValidarFlagDTO,
)
from modules.progress.application.queries.obtener_contenido_seccion import (
    ObtenerContenidoSeccionQuery,
)
from modules.progress.application.queries.obtener_examen import ObtenerExamenQuery
from modules.progress.application.queries.obtener_historial import ObtenerHistorialQuery
from modules.progress.application.queries.obtener_pista import ObtenerPistaQuery
from modules.progress.application.queries.obtener_progreso import ObtenerProgresoQuery
from modules.progress.application.use_cases.completar_seccion_teorica import (
    CompletarSeccionTeoricaUseCase,
)
from modules.progress.application.use_cases.enviar_examen import EnviarExamenUseCase
from modules.progress.application.use_cases.iniciar_examen import IniciarExamenUseCase
from modules.progress.application.use_cases.validar_flag import ValidarFlagUseCase
from modules.progress.infrastructure.asignacion_estado_provider import AsignacionEstadoProvider
from modules.progress.infrastructure.rate_limiter import ExamenRateLimiter, FlagRateLimiter
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.progress.presentation.serializers import (
    EnviarExamenRequestSerializer,
    ValidarFlagRequestSerializer,
)
from modules.shared.domain.exceptions import NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork

_ID_INVALIDO_MSG = "Progreso no encontrado."


def _parsear_uuid(valor: str) -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (ValueError, TypeError, AttributeError) as exc:
        raise NotFoundError(_ID_INVALIDO_MSG) from exc


class ProgresoOverviewView(APIView):
    """
    `GET /progress/{assignment_id}/` — resumen de secciones (con id, a
    diferencia del TOC público) + estado del examen, para la vista de
    "resolver laboratorio" del frontend.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, assignment_id):
        resultado = ObtenerProgresoQuery(
            progreso_repository=ProgresoRepository(),
            laboratorio_repository=LaboratorioRepository(),
            estado_asignacion_provider=AsignacionEstadoProvider(),
        ).execute(
            ObtenerProgresoDTO(
                asignacion_id=_parsear_uuid(assignment_id), estudiante_id=request.user.id
            )
        )

        return Response(
            {
                "asignacion_id": str(resultado.asignacion_id),
                "laboratorio_id": str(resultado.laboratorio_id),
                "laboratorio_nombre": resultado.laboratorio_nombre,
                "secciones_completas": resultado.secciones_completas,
                "examen_disponible": resultado.examen_disponible,
                "intentos_examen": resultado.intentos_examen,
                "vencido": resultado.vencido,
                "fecha_vencimiento": (
                    resultado.fecha_vencimiento.isoformat() if resultado.fecha_vencimiento else None
                ),
                "resumen_cierre": resultado.resumen_cierre,
                "secciones": [
                    {
                        "id": str(s.id),
                        "orden": s.orden,
                        "titulo": s.titulo,
                        "tiene_practica": s.tiene_practica,
                        "estado": s.estado,
                    }
                    for s in resultado.secciones
                ],
            },
            status=status.HTTP_200_OK,
        )


class ContenidoSeccionView(APIView):
    """`GET /progress/{assignment_id}/sections/{section_id}/` — HE-03/HE-04, api.md §7."""

    permission_classes = [IsAuthenticated]

    def get(self, request, assignment_id, section_id):
        resultado = ObtenerContenidoSeccionQuery(
            progreso_repository=ProgresoRepository(),
            laboratorio_repository=LaboratorioRepository(),
        ).execute(
            ObtenerContenidoSeccionDTO(
                asignacion_id=_parsear_uuid(assignment_id),
                seccion_id=_parsear_uuid(section_id),
                estudiante_id=request.user.id,
            )
        )

        return Response(
            {
                "seccion_id": str(resultado.seccion_id),
                "titulo": resultado.titulo,
                "contenido_teorico": resultado.contenido_teorico,
                "tiene_practica": resultado.tiene_practica,
                "estado": resultado.estado,
                "objetivos": resultado.objetivos,
                "duracion_estimada_minutos": resultado.duracion_estimada_minutos,
                "pasos_guia": resultado.pasos_guia,
                "entorno_practica": resultado.entorno_practica,
                "entorno_real_disponible": resultado.entorno_real_disponible,
            },
            status=status.HTTP_200_OK,
        )


class FlagValidationView(APIView):
    """
    `POST /progress/{assignment_id}/sections/{section_id}/flag/` —
    UC-02. Rate limit específico 20/min por usuario+sección
    (seguridad.md §5, api.md §12) antes de tocar el caso de uso.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, assignment_id, section_id):
        serializer = ValidarFlagRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        seccion_id = _parsear_uuid(section_id)
        FlagRateLimiter().verificar(estudiante_id=request.user.id, seccion_id=seccion_id)

        resultado = ValidarFlagUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            progreso_repository=ProgresoRepository(),
            laboratorio_repository=LaboratorioRepository(),
            estado_asignacion_provider=AsignacionEstadoProvider(),
        ).execute(
            ValidarFlagDTO(
                asignacion_id=_parsear_uuid(assignment_id),
                seccion_id=seccion_id,
                valor=serializer.validated_data["valor"],
                estudiante_id=request.user.id,
            )
        )

        if resultado.correcto:
            data = {
                "correcto": True,
                "seccion_desbloqueada": (
                    str(resultado.seccion_desbloqueada)
                    if resultado.seccion_desbloqueada
                    else None
                ),
            }
        else:
            data = {
                "correcto": False,
                "intentos_fallidos": resultado.intentos_fallidos,
                "pista_disponible": resultado.pista_disponible,
            }
            if resultado.pista_disponible:
                data["pista"] = resultado.pista
            if resultado.paso_a_paso_disponible:
                data["paso_a_paso_disponible"] = True
                data["paso_a_paso"] = resultado.paso_a_paso

        return Response(data, status=status.HTTP_200_OK)


class SectionCompletionView(APIView):
    """
    `POST /progress/{assignment_id}/sections/{section_id}/complete/` —
    UC-02 bis. Única forma de avanzar una sección sin práctica
    (`tiene_practica=False`, ej. una introducción teórica): no tiene flag
    que validar, así que no pasa por `FlagValidationView`. Sin esto, el
    frontend no tenía ningún botón/endpoint para "continuar" después de
    leer una sección puramente teórica y el laboratorio quedaba trabado.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, assignment_id, section_id):
        resultado = CompletarSeccionTeoricaUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            progreso_repository=ProgresoRepository(),
            laboratorio_repository=LaboratorioRepository(),
            estado_asignacion_provider=AsignacionEstadoProvider(),
        ).execute(
            CompletarSeccionTeoricaDTO(
                asignacion_id=_parsear_uuid(assignment_id),
                seccion_id=_parsear_uuid(section_id),
                estudiante_id=request.user.id,
            )
        )

        return Response(
            {
                "correcto": True,
                "seccion_desbloqueada": (
                    str(resultado.seccion_desbloqueada)
                    if resultado.seccion_desbloqueada
                    else None
                ),
            },
            status=status.HTTP_200_OK,
        )


class HintView(APIView):
    """`GET /progress/{assignment_id}/sections/{section_id}/hint/` — HE-06."""

    permission_classes = [IsAuthenticated]

    def get(self, request, assignment_id, section_id):
        resultado = ObtenerPistaQuery(
            progreso_repository=ProgresoRepository(),
            laboratorio_repository=LaboratorioRepository(),
        ).execute(
            ObtenerPistaDTO(
                asignacion_id=_parsear_uuid(assignment_id),
                seccion_id=_parsear_uuid(section_id),
                estudiante_id=request.user.id,
            )
        )

        data = {
            "intentos_fallidos": resultado.intentos_fallidos,
            "pista_disponible": resultado.pista_disponible,
            "paso_a_paso_disponible": resultado.paso_a_paso_disponible,
        }
        if resultado.pista_disponible:
            data["pista"] = resultado.pista
        if resultado.paso_a_paso_disponible:
            data["paso_a_paso"] = resultado.paso_a_paso

        return Response(data, status=status.HTTP_200_OK)


def _serializar_estado_examen(estado) -> dict:
    return {
        "examen_id": str(estado.examen_id),
        "total_preguntas": estado.total_preguntas,
        "max_intentos": estado.max_intentos,
        "puntaje_aprobacion": estado.puntaje_aprobacion,
        "intentos_restantes": estado.intentos_restantes,
        "bloqueado_hasta": estado.bloqueado_hasta.isoformat() if estado.bloqueado_hasta else None,
        "aprobado": estado.aprobado,
        "intentos_realizados": estado.intentos_realizados,
        "mejor_puntaje": estado.mejor_puntaje,
        "intento_abierto": estado.intento_abierto,
    }


class ExamSubmissionView(APIView):
    """
    `/progress/{assignment_id}/exam/` — HE-09/HI-08, UC-03. `GET` devuelve
    el estado de intentos (3 por ciclo, 24 h de espera tras reprobarlos);
    `POST` califica la entrega del intento abierto.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, assignment_id):
        estado = ObtenerExamenQuery(
            progreso_repository=ProgresoRepository(),
            laboratorio_repository=LaboratorioRepository(),
        ).execute(
            ObtenerExamenDTO(
                asignacion_id=_parsear_uuid(assignment_id), estudiante_id=request.user.id
            )
        )
        return Response(_serializar_estado_examen(estado), status=status.HTTP_200_OK)

    def post(self, request, assignment_id):
        serializer = EnviarExamenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ExamenRateLimiter().verificar(
            estudiante_id=request.user.id, asignacion_id=_parsear_uuid(assignment_id)
        )

        resultado = EnviarExamenUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            progreso_repository=ProgresoRepository(),
            laboratorio_repository=LaboratorioRepository(),
            estado_asignacion_provider=AsignacionEstadoProvider(),
        ).execute(
            EnviarExamenDTO(
                asignacion_id=_parsear_uuid(assignment_id),
                estudiante_id=request.user.id,
                respuestas=serializer.validated_data["respuestas"],
            )
        )

        return Response(
            {
                "puntaje": resultado.puntaje,
                "correctas": resultado.correctas,
                "total": resultado.total,
                "numero_intento": resultado.numero_intento,
                "aprobado": resultado.aprobado,
                "estado": _serializar_estado_examen(resultado.estado) if resultado.estado else None,
            },
            status=status.HTTP_200_OK,
        )


class ExamStartView(APIView):
    """
    `POST /progress/{assignment_id}/exam/iniciar/` — abre un intento y entrega
    las preguntas (nunca la respuesta correcta). Si había un intento abierto
    porque el estudiante salió sin entregar, ese cuenta como reprobado.
    Con el ciclo de 3 reprobado, responde `iniciado: false` y `bloqueado_hasta`.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, assignment_id):
        resultado = IniciarExamenUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            progreso_repository=ProgresoRepository(),
            laboratorio_repository=LaboratorioRepository(),
            estado_asignacion_provider=AsignacionEstadoProvider(),
        ).execute(
            IniciarExamenDTO(asignacion_id=_parsear_uuid(assignment_id), estudiante_id=request.user.id)
        )
        return Response(
            {
                "iniciado": resultado.iniciado,
                "iniciado_en": resultado.iniciado_en.isoformat() if resultado.iniciado_en else None,
                "abandono_cerrado": resultado.abandono_cerrado,
                "estado": _serializar_estado_examen(resultado.estado),
                "preguntas": [
                    {"id": str(p.id), "enunciado": p.enunciado, "tipo": p.tipo, "opciones": p.opciones}
                    for p in resultado.preguntas
                ],
            },
            status=status.HTTP_200_OK,
        )


class HistoryView(APIView):
    """`GET /progress/{assignment_id}/history/` — HE-10/HE-11."""

    permission_classes = [IsAuthenticated]

    def get(self, request, assignment_id):
        resultado = ObtenerHistorialQuery(progreso_repository=ProgresoRepository()).execute(
            ObtenerHistorialDTO(
                asignacion_id=_parsear_uuid(assignment_id),
                estudiante_id=request.user.id,
            )
        )

        return Response(
            [
                {
                    "numero_intento": item.numero_intento,
                    "fecha_completado": item.fecha_completado.isoformat(),
                    "puntaje": item.puntaje,
                }
                for item in resultado
            ],
            status=status.HTTP_200_OK,
        )
