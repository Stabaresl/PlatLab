from rest_framework import serializers


class EquiparCosmeticoRequestSerializer(serializers.Serializer):
    """`PATCH /gamification/cosmeticos/{id}/` — `true` equipa, `false` desequipa."""

    equipado = serializers.BooleanField()


class EquiparTituloRequestSerializer(serializers.Serializer):
    """`PATCH /gamification/titulos/{id}/` — `true` equipa, `false` desequipa."""

    equipado = serializers.BooleanField()


class CambiarAvatarRequestSerializer(serializers.Serializer):
    """`PATCH /gamification/avatar/` — elige un avatar predeterminado por su clave."""

    clave = serializers.CharField(max_length=100)


class SubirAvatarRequestSerializer(serializers.Serializer):
    """`POST /gamification/avatar/upload/` — multipart."""

    archivo = serializers.FileField()
