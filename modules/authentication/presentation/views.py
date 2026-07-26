from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.authentication.application.dtos import (
    ConfirmarRecuperacionDTO,
    LoginDTO,
    RefreshRequestDTO,
    RegistroDTO,
    SolicitarRecuperacionDTO,
)
from modules.authentication.application.use_cases.confirmar_recuperacion import (
    ConfirmarRecuperacionUseCase,
)
from modules.authentication.application.use_cases.login import LoginUseCase
from modules.authentication.application.use_cases.refresh_token import RefreshTokenUseCase
from modules.authentication.application.use_cases.registrar_usuario import (
    RegistrarUsuarioUseCase,
)
from modules.authentication.application.use_cases.solicitar_recuperacion import (
    SolicitarRecuperacionUseCase,
)
from modules.authentication.infrastructure.jwt_service import JWTService
from modules.authentication.infrastructure.password_reset_store import (
    PasswordResetTokenStore,
)
from modules.authentication.infrastructure.refresh_token_store import RefreshTokenStore
from modules.authentication.presentation.serializers import (
    ConfirmarRecuperacionRequestSerializer,
    LoginRequestSerializer,
    RefreshRequestSerializer,
    RegistroRequestSerializer,
    SolicitarRecuperacionRequestSerializer,
)
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.infrastructure.repositories import UserRepository


class RegisterView(APIView):
    """POST /api/v1/auth/register/ — UC-01 flujo principal (HV-04)."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistroRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = RegistrarUsuarioUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            user_repository=UserRepository(),
        )
        result = use_case.execute(RegistroDTO(**serializer.validated_data))

        return Response(
            {
                "id": str(result.id),
                "email": result.email,
                "rol": result.rol,
                "email_verificado": result.email_verificado,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """POST /api/v1/auth/login/ — UC-01 flujo A2 (RF-02)."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = LoginUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            user_repository=UserRepository(),
            jwt_service=JWTService(),
            refresh_token_store=RefreshTokenStore(),
        )
        tokens = use_case.execute(LoginDTO(**serializer.validated_data))

        return Response(
            {
                "access": tokens.access,
                "refresh": tokens.refresh,
                "expires_in": tokens.expires_in,
                "rol": tokens.rol,
            },
            status=status.HTTP_200_OK,
        )


class RefreshTokenView(APIView):
    """POST /api/v1/auth/refresh/ — rota el refresh token (RF-07)."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = RefreshTokenUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            jwt_service=JWTService(),
            refresh_token_store=RefreshTokenStore(),
        )
        tokens = use_case.execute(RefreshRequestDTO(**serializer.validated_data))

        return Response(
            {
                "access": tokens.access,
                "refresh": tokens.refresh,
                "expires_in": tokens.expires_in,
                "rol": tokens.rol,
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetView(APIView):
    """POST /api/v1/auth/password-reset/ — UC-01 A3, paso 1-2 (HV-05, RF-03)."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SolicitarRecuperacionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = SolicitarRecuperacionUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            user_repository=UserRepository(),
            password_reset_store=PasswordResetTokenStore(),
        )
        use_case.execute(SolicitarRecuperacionDTO(**serializer.validated_data))

        # Respuesta genérica siempre igual, exista o no el correo
        # (anti-enumeración, UC-01 E1).
        return Response(
            {"message": "Si el correo está registrado, recibirás un enlace de recuperación."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """POST /api/v1/auth/password-reset/confirm/ — UC-01 A3, paso 3c."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ConfirmarRecuperacionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = ConfirmarRecuperacionUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            user_repository=UserRepository(),
            password_reset_store=PasswordResetTokenStore(),
            refresh_token_store=RefreshTokenStore(),
        )
        use_case.execute(ConfirmarRecuperacionDTO(**serializer.validated_data))

        return Response(
            {"message": "Contraseña actualizada correctamente."},
            status=status.HTTP_200_OK,
        )
