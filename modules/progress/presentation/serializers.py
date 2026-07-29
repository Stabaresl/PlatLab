from rest_framework import serializers


class ValidarFlagRequestSerializer(serializers.Serializer):
    """api.md §7 — DTO de entrada de `POST .../flag/` (UC-02)."""

    valor = serializers.CharField(max_length=500, trim_whitespace=False)


class EnviarExamenRequestSerializer(serializers.Serializer):
    """api.md §7 — DTO de entrada de `POST .../exam/` (HE-09/HI-08, UC-03)."""

    respuestas = serializers.DictField(
        child=serializers.CharField(trim_whitespace=False), allow_empty=True
    )
