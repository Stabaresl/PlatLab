from rest_framework import serializers

from modules.reports.domain.value_objects import EstadoReporte

_ESTADO_CHOICES = [e.value for e in EstadoReporte]


class CrearReporteRequestSerializer(serializers.Serializer):
    """api.md §8 `POST /reports/` (UC-09) — multipart, `adjunto` opcional."""

    laboratorio_id = serializers.UUIDField()
    seccion_id = serializers.UUIDField(required=False, allow_null=True)
    descripcion = serializers.CharField()
    adjunto = serializers.FileField(required=False, allow_null=True)


class CambiarEstadoReporteRequestSerializer(serializers.Serializer):
    """
    api.md §8 `PATCH /reports/{id}/`. `abierto` no es una transición (es el
    estado inicial): antes pasaba esta validación y el caso de uso caía
    con KeyError -> 500.
    """

    estado = serializers.ChoiceField(
        choices=[e.value for e in EstadoReporte if e != EstadoReporte.ABIERTO]
    )


class ListarReportesQuerySerializer(serializers.Serializer):
    """api.md §8 `GET /reports/?estado=&laboratorio=` — solo Admin."""

    estado = serializers.ChoiceField(choices=_ESTADO_CHOICES, required=False)
    laboratorio = serializers.UUIDField(required=False)
