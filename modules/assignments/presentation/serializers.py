from rest_framework import serializers


class InvitarEstudiantesRequestSerializer(serializers.Serializer):
    """api.md §6 — DTO de entrada `POST /assignments/invitations/` (UC-06)."""

    laboratorio_id = serializers.UUIDField()
    estudiantes = serializers.ListField(
        child=serializers.CharField(max_length=255), allow_empty=False
    )
    fecha_vencimiento = serializers.DateTimeField(required=False, allow_null=True)


class FiltrarEstudiantesQuerySerializer(serializers.Serializer):
    """HI-04 — query params `?nombre=&laboratorio_id=`."""

    nombre = serializers.CharField(required=False, max_length=200)
    laboratorio_id = serializers.UUIDField(required=False)
