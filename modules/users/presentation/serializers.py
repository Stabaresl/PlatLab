import re

from rest_framework import serializers

from modules.users.domain.value_objects import Rol

_ROL_CHOICES = [r.value for r in Rol]
_TIPOS_INSTRUCTOR = ["profesor", "capacitador", "investigador", "independiente"]
_ORCID_REGEX = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")


class ListarUsuariosQuerySerializer(serializers.Serializer):
    """HA-01, api.md §4 `GET /users/?nombre=&rol=&activo=`."""

    nombre = serializers.CharField(required=False, max_length=200)
    rol = serializers.ChoiceField(choices=_ROL_CHOICES, required=False)
    # `allow_null=True` es necesario: sin él, DRF trata un query param
    # ausente como `False` (comportamiento HTML-input de BooleanField),
    # filtrando por defecto solo usuarios deshabilitados en vez de no
    # filtrar por `activo` en absoluto.
    activo = serializers.BooleanField(required=False, allow_null=True)


class ActualizarUsuarioRequestSerializer(serializers.Serializer):
    """HA-01, api.md §4 `PATCH /users/{id}/`."""

    nombre_completo = serializers.CharField(max_length=200, required=False)
    rol = serializers.ChoiceField(choices=_ROL_CHOICES, required=False)
    username = serializers.CharField(max_length=50, required=False, allow_null=True)


class SolicitarInstructorRequestSerializer(serializers.Serializer):
    """`POST /users/instructor-requests/` — solicitud de instructor verificada vía OpenAlex."""

    orcid = serializers.RegexField(
        regex=_ORCID_REGEX,
        error_messages={"invalid": "El ORCID no tiene un formato válido (0000-0000-0000-0000)."},
    )
    tipo = serializers.ChoiceField(choices=_TIPOS_INSTRUCTOR)
    institucion = serializers.CharField(max_length=200, required=False, allow_blank=True)
    especialidades = serializers.CharField(max_length=300, required=False, allow_blank=True)
    motivacion = serializers.CharField(max_length=1000, required=False, allow_blank=True)
