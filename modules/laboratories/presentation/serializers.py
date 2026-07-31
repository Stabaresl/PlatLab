from rest_framework import serializers

from modules.laboratories.domain.value_objects import (
    ComandoSimulado,
    EntornoPractica,
    NivelDificultad,
    PasoGuia,
    TipoPregunta,
)
from modules.laboratories.infrastructure.markdown_renderer import renderizar_markdown


def _markdown_a_html(texto: str) -> str:
    """
    El instructor escribe/sube Markdown (wizard de creación) — se convierte
    a HTML acá, en Presentación, antes de que el texto llegue al DTO/caso
    de uso. El caso de uso sigue recibiendo y saneando HTML exactamente
    como antes (`sanitizar_contenido_html` ya corre ahí) — este helper solo
    agrega el paso Markdown→HTML, nunca reemplaza el saneo.
    """
    return renderizar_markdown(texto)


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
    resumen_cierre = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_resumen_cierre(self, value: str) -> str:
        return _markdown_a_html(value)


class EditarLaboratorioRequestSerializer(serializers.Serializer):
    """api.md §5 `PATCH /laboratories/{id}/`."""

    nombre = serializers.CharField(max_length=200, required=False)
    descripcion = serializers.CharField(required=False)
    nivel_dificultad = serializers.ChoiceField(
        choices=[nivel.value for nivel in NivelDificultad], required=False
    )
    temas = serializers.ListField(child=serializers.CharField(max_length=100), required=False)
    resumen_cierre = serializers.CharField(required=False, allow_blank=True)

    def validate_resumen_cierre(self, value: str) -> str:
        return _markdown_a_html(value)


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


class PasoGuiaRequestSerializer(serializers.Serializer):
    """Un paso numerado de la guía de una sección (ver `PasoGuia` en el dominio)."""

    orden = serializers.IntegerField(min_value=1)
    titulo = serializers.CharField(max_length=200)
    instrucciones = serializers.CharField()
    comando_sugerido = serializers.CharField(
        max_length=500, required=False, allow_null=True, trim_whitespace=False
    )

    def create(self, validated_data):
        return PasoGuia(
            orden=validated_data["orden"],
            titulo=validated_data["titulo"],
            instrucciones=_markdown_a_html(validated_data["instrucciones"]),
            comando_sugerido=validated_data.get("comando_sugerido"),
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
    objetivos = serializers.ListField(
        child=serializers.CharField(max_length=300), required=False, default=list
    )
    duracion_estimada_minutos = serializers.IntegerField(min_value=1, required=False, default=15)
    pasos_guia = PasoGuiaRequestSerializer(many=True, required=False, default=list)
    entorno_practica = EntornoPracticaRequestSerializer(required=False, allow_null=True)
    imagen_practica = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=False)

    def validate_contenido_teorico(self, value: str) -> str:
        return _markdown_a_html(value)


class EditarSeccionRequestSerializer(serializers.Serializer):
    """api.md §5 `PATCH /laboratories/{id}/sections/{section_id}/`."""

    titulo = serializers.CharField(max_length=200, required=False)
    contenido_teorico = serializers.CharField(required=False)
    orden = serializers.IntegerField(min_value=1, required=False)
    tiene_practica = serializers.BooleanField(required=False)
    objetivos = serializers.ListField(child=serializers.CharField(max_length=300), required=False)
    duracion_estimada_minutos = serializers.IntegerField(min_value=1, required=False)
    pasos_guia = PasoGuiaRequestSerializer(many=True, required=False)
    entorno_practica = EntornoPracticaRequestSerializer(required=False, allow_null=True)
    imagen_practica = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=False)

    def validate_contenido_teorico(self, value: str) -> str:
        return _markdown_a_html(value)


class RechazarLaboratorioRequestSerializer(serializers.Serializer):
    """`POST /laboratories/{id}/reject/` — motivo obligatorio, visible para el instructor."""

    motivo = serializers.CharField(max_length=1000, trim_whitespace=True)


class SubirDockerfileRequestSerializer(serializers.Serializer):
    """
    `POST /laboratories/{id}/sections/{section_id}/dockerfile/` —
    multipart. Nunca se ejecuta ni se construye nada acá: solo se guarda
    para revisión manual del admin.
    """

    archivo = serializers.FileField()


class PreviewFlagRequestSerializer(serializers.Serializer):
    """`POST .../preview/check-flag/` — solo verifica, no persiste intentos."""

    valor = serializers.CharField(max_length=500, trim_whitespace=False)


class AgregarPreguntaRequestSerializer(serializers.Serializer):
    """api.md §5 `POST /laboratories/{id}/exam/questions/` (HE-09/HI-08)."""

    enunciado = serializers.CharField()
    tipo = serializers.ChoiceField(choices=[tipo.value for tipo in TipoPregunta])
    respuesta = serializers.CharField(max_length=500, trim_whitespace=False)
    opciones = serializers.ListField(
        child=serializers.CharField(max_length=200), required=False, allow_null=True
    )
