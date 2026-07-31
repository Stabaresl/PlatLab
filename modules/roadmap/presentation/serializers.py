from rest_framework import serializers


class CrearCategoriaRequestSerializer(serializers.Serializer):
    """`POST /roadmap/categorias/`."""

    nombre = serializers.CharField(max_length=100)


class AgregarNodoRequestSerializer(serializers.Serializer):
    """`POST /roadmap/nodos/` — `posicion` es opcional: si se omite, se agrega al final de la categoría."""

    categoria_id = serializers.UUIDField()
    laboratorio_id = serializers.UUIDField()
    posicion = serializers.IntegerField(min_value=0, required=False)


class ReordenarNodoRequestSerializer(serializers.Serializer):
    """`PATCH /roadmap/nodos/{id}/`."""

    categoria_id = serializers.UUIDField()
    posicion = serializers.IntegerField(min_value=0)
