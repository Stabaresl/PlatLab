from rest_framework import serializers


class RegistroRequestSerializer(serializers.Serializer):
    """
    Valida únicamente forma/tipo de los datos (campos requeridos, formato
    básico de email). Las reglas de negocio (política de contraseña,
    unicidad) se validan en `RegistrarUsuarioUseCase` — Presentation nunca
    duplica lógica de negocio, solo la forma del dato de entrada.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)
    nombre_completo = serializers.CharField(max_length=200)


class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
