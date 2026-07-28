from rest_framework import serializers


class ValidarFlagRequestSerializer(serializers.Serializer):
    """api.md §7 — DTO de entrada de `POST .../flag/` (UC-02)."""

    valor = serializers.CharField(max_length=500, trim_whitespace=False)
