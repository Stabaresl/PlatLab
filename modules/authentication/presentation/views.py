from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.authentication.application.dtos import LoginDTO, RegistroDTO
from modules.authentication.application.use_cases.login import LoginUseCase
from modules.authentication.application.use_cases.registrar_usuario import (
    RegistrarUsuarioUseCase,
)
from modules.authentication.infrastructure.jwt_service import JWTService
from modules.authentication.presentation.serializers import (
    LoginRequestSerializer,
    RegistroRequestSerializer,
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
