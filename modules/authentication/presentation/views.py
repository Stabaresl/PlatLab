from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.authentication.application.dtos import (
    ConfirmarRecuperacionDTO,
    ConfirmarVinculacionDTO,
    LoginDTO,
    OAuthAuthorizeDTO,
    OAuthCallbackDTO,
    RefreshRequestDTO,
    RegistroDTO,
    SolicitarRecuperacionDTO,
)
from modules.authentication.application.use_cases.confirmar_recuperacion import (
    ConfirmarRecuperacionUseCase,
)
from modules.authentication.application.use_cases.confirmar_vinculacion_oauth import (
    ConfirmarVinculacionOAuthUseCase,
)
from modules.authentication.application.use_cases.iniciar_oauth import IniciarOAuthUseCase
from modules.authentication.application.use_cases.login import LoginUseCase
from modules.authentication.application.use_cases.oauth_login import OAuthLoginUseCase
from modules.authentication.application.use_cases.refresh_token import RefreshTokenUseCase
from modules.authentication.application.use_cases.registrar_usuario import (
    RegistrarUsuarioUseCase,
)
from modules.authentication.application.use_cases.solicitar_recuperacion import (
    SolicitarRecuperacionUseCase,
)
from modules.authentication.domain.services import VinculadorDeCuenta
from modules.authentication.infrastructure.jwt_service import JWTService
from modules.authentication.infrastructure.oauth_adapters import (
    GitHubOAuthAdapter,
    GoogleOAuthAdapter,
)
from modules.authentication.infrastructure.oauth_link_store import OAuthLinkStore
from modules.authentication.infrastructure.oauth_state_store import OAuthStateStore
from modules.authentication.infrastructure.password_reset_store import (
    PasswordResetTokenStore,
)
from modules.authentication.infrastructure.refresh_token_store import RefreshTokenStore
from modules.authentication.presentation.serializers import (
    ConfirmarRecuperacionRequestSerializer,
    LoginRequestSerializer,
    OAuthCallbackRequestSerializer,
    OAuthConfirmLinkRequestSerializer,
    RefreshRequestSerializer,
    RegistroRequestSerializer,
    SolicitarRecuperacionRequestSerializer,
)
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.infrastructure.repositories import UserRepository

_OAUTH_ADAPTERS = {
    "google": GoogleOAuthAdapter,
    "github": GitHubOAuthAdapter,
}


def _resolve_adapter(proveedor: str):
    adapter_cls = _OAUTH_ADAPTERS.get(proveedor)
    if adapter_cls is None:
        raise NotFound(f"Proveedor OAuth no soportado: {proveedor}")
    return adapter_cls()


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


class OAuthAuthorizeView(APIView):
    """GET /api/v1/auth/oauth/<provider>/authorize/ — UC-01 A1, paso 1a (HV-04)."""

    permission_classes = [AllowAny]

    def get(self, request, provider):
        use_case = IniciarOAuthUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            oauth_adapter=_resolve_adapter(provider),
            oauth_state_store=OAuthStateStore(),
        )
        result = use_case.execute(OAuthAuthorizeDTO(proveedor=provider))

        return Response(
            {"authorize_url": result.authorize_url, "state": result.state},
            status=status.HTTP_200_OK,
        )


class OAuthCallbackView(APIView):
    """POST /api/v1/auth/oauth/<provider>/callback/ — UC-01 A1/A2 vía OAuth (HV-04)."""

    permission_classes = [AllowAny]

    def post(self, request, provider):
        adapter = _resolve_adapter(provider)
        serializer = OAuthCallbackRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = OAuthLoginUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            user_repository=UserRepository(),
            jwt_service=JWTService(),
            refresh_token_store=RefreshTokenStore(),
            oauth_state_store=OAuthStateStore(),
            oauth_link_store=OAuthLinkStore(),
            oauth_adapter=adapter,
            vinculador_de_cuenta=VinculadorDeCuenta(),
        )
        result = use_case.execute(
            OAuthCallbackDTO(
                proveedor=provider,
                code=serializer.validated_data["code"],
                state=serializer.validated_data["state"],
            )
        )

        return Response(
            {
                "access": result.tokens.access,
                "refresh": result.tokens.refresh,
                "expires_in": result.tokens.expires_in,
                "rol": result.tokens.rol,
            },
            status=status.HTTP_200_OK,
        )


class OAuthConfirmLinkView(APIView):
    """
    POST /api/v1/auth/oauth/confirm-link/ — UC-01 E4: confirmación
    explícita (reautenticación con password) de una vinculación OAuth
    pendiente por colisión de email (`VinculadorDeCuenta`).
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OAuthConfirmLinkRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = ConfirmarVinculacionOAuthUseCase(
            unit_of_work=BaseUnitOfWork(),
            event_dispatcher=EventDispatcher(),
            user_repository=UserRepository(),
            jwt_service=JWTService(),
            refresh_token_store=RefreshTokenStore(),
            oauth_link_store=OAuthLinkStore(),
        )
        tokens = use_case.execute(ConfirmarVinculacionDTO(**serializer.validated_data))

        return Response(
            {
                "access": tokens.access,
                "refresh": tokens.refresh,
                "expires_in": tokens.expires_in,
                "rol": tokens.rol,
            },
            status=status.HTTP_200_OK,
        )
