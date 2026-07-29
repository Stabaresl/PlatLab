from rest_framework import serializers


class ListarNotificacionesQuerySerializer(serializers.Serializer):
    # BooleanField sin allow_null trata query param ausente como False
    # (gotcha DRF con QueryDict, ver modules/users/presentation/serializers.py).
    leida = serializers.BooleanField(required=False, allow_null=True)
