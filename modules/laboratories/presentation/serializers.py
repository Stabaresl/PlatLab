from rest_framework import serializers

from modules.laboratories.domain.value_objects import NivelDificultad


class CatalogoFiltroQuerySerializer(serializers.Serializer):
    """
    Valida forma de los query params `?dificultad=&tema=` (HV-02, RF-06).
    Las choices salen de `NivelDificultad` (Domain), no del modelo ORM —
    Presentation no debe conocer Infrastructure directamente (backend.md).
    """

    dificultad = serializers.ChoiceField(
        choices=[nivel.value for nivel in NivelDificultad], required=False
    )
    tema = serializers.CharField(required=False, max_length=100)
