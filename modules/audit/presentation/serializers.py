from rest_framework import serializers


class ConsultarAuditoriaQuerySerializer(serializers.Serializer):
    actor = serializers.UUIDField(required=False, allow_null=True)
    accion = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    desde = serializers.DateTimeField(required=False, allow_null=True)
    hasta = serializers.DateTimeField(required=False, allow_null=True)
