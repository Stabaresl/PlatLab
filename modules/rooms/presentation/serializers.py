from rest_framework import serializers

from modules.rooms.domain.value_objects import CAPACIDAD_MAXIMA


class CrearSalaRequestSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=120)
    laboratorio_id = serializers.UUIDField()
    descripcion = serializers.CharField(max_length=1000, required=False, allow_blank=True, default="")
    capacidad = serializers.IntegerField(min_value=1, max_value=CAPACIDAD_MAXIMA, required=False, default=30)
    fecha_fin = serializers.DateTimeField(required=False, allow_null=True, default=None)


class UnirseSalaRequestSerializer(serializers.Serializer):
    codigo = serializers.CharField(max_length=20)


class CambiarEstadoSalaRequestSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=["abierta", "cerrada", "finalizada"])
