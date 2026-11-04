import uuid

from django.db.models import Q
from django.utils import timezone

from modules.progress.domain.entities import (
    HistorialCompletitud,
    IntentoFlag,
    Progreso,
    ProgresoSeccion,
    ResultadoExamen,
)
from modules.progress.domain.value_objects import PUNTAJE_APROBACION, EstadoProgresoSeccion
from modules.progress.infrastructure.mappers import (
    historial_to_entity,
    intento_flag_to_entity,
    progreso_seccion_to_entity,
    progreso_to_entity,
    resultado_examen_to_entity,
)
from modules.progress.infrastructure.models import (
    HistorialCompletitudModel,
    IntentoFlagModel,
    ProgresoModel,
    ProgresoSeccionModel,
    ResultadoExamenModel,
)

# "Terminado" = laboratorio sin examen (historial sin puntaje) o examen aprobado.
# Presentar el examen y reprobarlo deja historial, pero no termina el laboratorio.
_HISTORIAL_APROBADO = Q(puntaje__isnull=True) | Q(puntaje__gte=PUNTAJE_APROBACION)


class ProgresoRepository:
    """
    Implementación de `IProgresoRepository`
    (modules.progress.domain.repositories) sobre PostgreSQL vía el ORM
    de Django — traduce entidad <-> modelo con `mappers.py` en cada
    operación.
    """

    def get_by_asignacion(self, asignacion_id: uuid.UUID) -> Progreso | None:
        model = ProgresoModel.objects.filter(asignacion_id=asignacion_id).first()
        return progreso_to_entity(model) if model else None

    def get_by_id(self, progreso_id: uuid.UUID) -> Progreso | None:
        model = ProgresoModel.objects.filter(id=progreso_id).first()
        return progreso_to_entity(model) if model else None

    def add(self, progreso: Progreso) -> Progreso:
        model = ProgresoModel.objects.create(
            id=progreso.id,
            asignacion_id=progreso.asignacion_id,
            estudiante_id=progreso.estudiante_id,
        )
        return progreso_to_entity(model)

    def tocar_actividad(self, progreso_id: uuid.UUID) -> None:
        ProgresoModel.objects.filter(id=progreso_id).update(ultima_actividad=timezone.now())

    def get_secciones(self, progreso_id: uuid.UUID) -> list[ProgresoSeccion]:
        modelos = ProgresoSeccionModel.objects.filter(progreso_id=progreso_id)
        return [progreso_seccion_to_entity(m) for m in modelos]

    def get_completitud_por_asignaciones(
        self, asignacion_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, float]:
        if not asignacion_ids:
            return {}

        progreso_id_por_asignacion = dict(
            ProgresoModel.objects.filter(asignacion_id__in=asignacion_ids).values_list(
                "asignacion_id", "id"
            )
        )
        if not progreso_id_por_asignacion:
            return {}

        total_por_progreso: dict[uuid.UUID, int] = {}
        completadas_por_progreso: dict[uuid.UUID, int] = {}
        secciones = ProgresoSeccionModel.objects.filter(
            progreso_id__in=progreso_id_por_asignacion.values()
        ).values_list("progreso_id", "estado")
        for progreso_id, estado in secciones:
            total_por_progreso[progreso_id] = total_por_progreso.get(progreso_id, 0) + 1
            if estado == EstadoProgresoSeccion.COMPLETADA.value:
                completadas_por_progreso[progreso_id] = (
                    completadas_por_progreso.get(progreso_id, 0) + 1
                )

        resultado: dict[uuid.UUID, float] = {}
        for asignacion_id, progreso_id in progreso_id_por_asignacion.items():
            total = total_por_progreso.get(progreso_id, 0)
            if total == 0:
                continue
            completadas = completadas_por_progreso.get(progreso_id, 0)
            resultado[asignacion_id] = completadas / total * 100
        return resultado

    def resumen_por_asignaciones(self, asignacion_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict]:
        if not asignacion_ids:
            return {}
        progresos = {
            pid: {"asignacion_id": aid, "ultima_actividad": ultima}
            for pid, aid, ultima in ProgresoModel.objects.filter(
                asignacion_id__in=asignacion_ids
            ).values_list("id", "asignacion_id", "ultima_actividad")
        }
        if not progresos:
            return {}

        resumen: dict[uuid.UUID, dict] = {
            datos["asignacion_id"]: {
                "secciones_completadas": 0,
                "secciones_total": 0,
                "mejor_puntaje": None,
                "completado": False,
                "fecha_completado": None,
                "ultima_actividad": datos["ultima_actividad"],
            }
            for datos in progresos.values()
        }

        def _de(progreso_id):
            return resumen[progresos[progreso_id]["asignacion_id"]]

        for progreso_id, estado in ProgresoSeccionModel.objects.filter(
            progreso_id__in=progresos.keys()
        ).values_list("progreso_id", "estado"):
            fila = _de(progreso_id)
            fila["secciones_total"] += 1
            if estado == EstadoProgresoSeccion.COMPLETADA.value:
                fila["secciones_completadas"] += 1

        for progreso_id, puntaje in ResultadoExamenModel.objects.filter(
            progreso_id__in=progresos.keys()
        ).values_list("progreso_id", "puntaje"):
            fila = _de(progreso_id)
            valor = float(puntaje)
            if fila["mejor_puntaje"] is None or valor > fila["mejor_puntaje"]:
                fila["mejor_puntaje"] = valor

        for progreso_id, fecha in HistorialCompletitudModel.objects.filter(
            _HISTORIAL_APROBADO, progreso_id__in=progresos.keys()
        ).values_list("progreso_id", "fecha_completado"):
            fila = _de(progreso_id)
            fila["completado"] = True
            if fila["fecha_completado"] is None or fecha < fila["fecha_completado"]:
                fila["fecha_completado"] = fecha

        return resumen

    def asignaciones_con_historial(self, asignacion_ids: list[uuid.UUID]) -> set[uuid.UUID]:
        """Batch: de estas asignaciones, cuáles tienen ≥1 `HistorialCompletitud` (laboratorio terminado)."""
        if not asignacion_ids:
            return set()
        aprobadas = HistorialCompletitudModel.objects.filter(
            _HISTORIAL_APROBADO, progreso__asignacion_id__in=asignacion_ids
        ).values_list("progreso__asignacion_id", flat=True)
        return set(aprobadas)

    def get_seccion(
        self, progreso_id: uuid.UUID, seccion_id: uuid.UUID
    ) -> ProgresoSeccion | None:
        model = ProgresoSeccionModel.objects.filter(
            progreso_id=progreso_id, seccion_id=seccion_id
        ).first()
        return progreso_seccion_to_entity(model) if model else None

    def add_secciones(self, secciones: list[ProgresoSeccion]) -> list[ProgresoSeccion]:
        modelos = ProgresoSeccionModel.objects.bulk_create(
            [
                ProgresoSeccionModel(
                    id=s.id,
                    progreso_id=s.progreso_id,
                    seccion_id=s.seccion_id,
                    estado=s.estado.value,
                    fecha_completado=s.fecha_completado,
                )
                for s in secciones
            ]
        )
        return [progreso_seccion_to_entity(m) for m in modelos]

    def actualizar_seccion(self, seccion: ProgresoSeccion) -> ProgresoSeccion:
        ProgresoSeccionModel.objects.filter(id=seccion.id).update(
            estado=seccion.estado.value,
            fecha_completado=seccion.fecha_completado,
        )
        return seccion

    def registrar_intento(self, intento: IntentoFlag) -> IntentoFlag:
        model = IntentoFlagModel.objects.create(
            id=intento.id,
            progreso_id=intento.progreso_id,
            seccion_id=intento.seccion_id,
            resultado=intento.resultado,
        )
        return intento_flag_to_entity(model)

    def contar_fallos(self, progreso_id: uuid.UUID, seccion_id: uuid.UUID) -> int:
        return IntentoFlagModel.objects.filter(
            progreso_id=progreso_id, seccion_id=seccion_id, resultado=False
        ).count()

    def registrar_historial(self, historial: HistorialCompletitud) -> HistorialCompletitud:
        model = HistorialCompletitudModel.objects.create(
            id=historial.id,
            progreso_id=historial.progreso_id,
            numero_intento=historial.numero_intento,
            puntaje=historial.puntaje,
        )
        return historial_to_entity(model)

    def get_historial(self, progreso_id: uuid.UUID) -> list[HistorialCompletitud]:
        modelos = HistorialCompletitudModel.objects.filter(
            progreso_id=progreso_id
        ).order_by("numero_intento")
        return [historial_to_entity(m) for m in modelos]

    def registrar_resultado_examen(self, resultado: ResultadoExamen) -> ResultadoExamen:
        model = ResultadoExamenModel.objects.create(
            id=resultado.id,
            progreso_id=resultado.progreso_id,
            examen_id=resultado.examen_id,
            respuestas=resultado.respuestas,
            puntaje=resultado.puntaje,
        )
        return resultado_examen_to_entity(model)

    def get_resultados_examen(self, progreso_id: uuid.UUID) -> list[ResultadoExamen]:
        modelos = ResultadoExamenModel.objects.filter(progreso_id=progreso_id).order_by("fecha")
        return [resultado_examen_to_entity(m) for m in modelos]

    def bloquear(self, progreso_id: uuid.UUID) -> Progreso:
        return progreso_to_entity(ProgresoModel.objects.select_for_update().get(id=progreso_id))

    def fijar_examen_iniciado(self, progreso_id: uuid.UUID, cuando) -> None:
        ProgresoModel.objects.filter(id=progreso_id).update(examen_iniciado_en=cuando)
