from rest_framework import serializers

from modules.laboratories.domain.value_objects import (
    ComandoSimulado,
    EntornoPractica,
    NivelDificultad,
    TipoPregunta,
)


class CatalogoFiltroQuerySerializer(serializers.Serializer):
    """
    Valida forma de los query params `?dificultad=&tema=&nombre=` (HV-02,
    RF-06, HI-05). Las choices salen de `NivelDificultad` (Domain), no
    del modelo ORM — Presentation no debe conocer Infrastructure
    directamente (backend.md).
    """

    dificultad = serializers.ChoiceField(
        choices=[nivel.value for nivel in NivelDificultad], required=False
    )
    tema = serializers.CharField(required=False, max_length=100)
    nombre = serializers.CharField(required=False, max_length=200)


class DefinirFlagRequestSerializer(serializers.Serializer):
    """api.md §5 — DTO de entrada de `PUT .../flag/` (write-only)."""

    valor = serializers.CharField(max_length=500, trim_whitespace=False)
    pista = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    paso_a_paso = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class CrearLaboratorioRequestSerializer(serializers.Serializer):
    """api.md §5 `POST /laboratories/` (UC-04)."""

    nombre = serializers.CharField(max_length=200)
    descripcion = serializers.CharField()
    nivel_dificultad = serializers.ChoiceField(choices=[nivel.value for nivel in NivelDificultad])
    temas = serializers.ListField(
        child=serializers.CharField(max_length=100), required=False, default=list
    )


class EditarLaboratorioRequestSerializer(serializers.Serializer):
    """api.md §5 `PATCH /laboratories/{id}/`."""

    nombre = serializers.CharField(max_length=200, required=False)
    descripcion = serializers.CharField(required=False)
    nivel_dificultad = serializers.ChoiceField(
        choices=[nivel.value for nivel in NivelDificultad], required=False
    )
    temas = serializers.ListField(child=serializers.CharField(max_length=100), required=False)


class ComandoSimuladoRequestSerializer(serializers.Serializer):
    """Un par comando/salida de la consola simulada (ver `EntornoPractica`)."""

    comando = serializers.CharField(max_length=200, trim_whitespace=False)
    salida = serializers.CharField(trim_whitespace=False)


class EntornoPracticaRequestSerializer(serializers.Serializer):
    """
    Guion completo de la consola simulada de una sección práctica —
    autoría del instructor/administrador, sin ejecución real (ver
    `EntornoPractica` en el dominio).
    """

    prompt = serializers.CharField(max_length=100, required=False, default="root@lab:~#")
    banner = serializers.CharField(required=False, allow_blank=True, default="")
    comandos = ComandoSimuladoRequestSerializer(many=True, required=False, default=list)

    def create(self, validated_data):
        return EntornoPractica(
            prompt=validated_data["prompt"],
            banner=validated_data["banner"],
            comandos=[
                ComandoSimulado(comando=c["comando"], salida=c["salida"])
                for c in validated_data["comandos"]
            ],
        )

    def to_internal_value(self, data):
        validated = super().to_internal_value(data)
        return self.create(validated)


class CrearSeccionRequestSerializer(serializers.Serializer):
    """api.md §5 `POST /laboratories/{id}/sections/`."""

    titulo = serializers.CharField(max_length=200)
    contenido_teorico = serializers.CharField()
    orden = serializers.IntegerField(min_value=1)
    tiene_practica = serializers.BooleanField(required=False, default=False)
    guia_paso_a_paso = serializers.CharField(required=False, allow_blank=True, default="")
    entorno_practica = EntornoPracticaRequestSerializer(required=False, allow_null=True)
    imagen_practica = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=False)


class EditarSeccionRequestSerializer(serializers.Serializer):
    """api.md §5 `PATCH /laboratories/{id}/sections/{section_id}/`."""

    titulo = serializers.CharField(max_length=200, required=False)
    contenido_teorico = serializers.CharField(required=False)
    orden = serializers.IntegerField(min_value=1, required=False)
    tiene_practica = serializers.BooleanField(required=False)
    guia_paso_a_paso = serializers.CharField(required=False, allow_blank=True)
    entorno_practica = EntornoPracticaRequestSerializer(required=False, allow_null=True)
    imagen_practica = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=False)


class AgregarPreguntaRequestSerializer(serializers.Serializer):
    """api.md §5 `POST /laboratories/{id}/exam/questions/` (HE-09/HI-08)."""

    enunciado = serializers.CharField()
    tipo = serializers.ChoiceField(choices=[tipo.value for tipo in TipoPregunta])
    respuesta = serializers.CharField(max_length=500, trim_whitespace=False)
    opciones = serializers.ListField(
        child=serializers.CharField(max_length=200), required=False, allow_null=True
    )
