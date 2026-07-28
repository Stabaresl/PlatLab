from django.urls import path

from modules.authentication.presentation.views import (
    LoginView,
    OAuthAuthorizeView,
    OAuthCallbackView,
    OAuthConfirmLinkView,
    PasswordResetConfirmView,
    PasswordResetView,
    RefreshTokenView,
    RegisterView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshTokenView.as_view(), name="auth-refresh"),
    path("password-reset/", PasswordResetView.as_view(), name="auth-password-reset"),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
    path(
        "oauth/confirm-link/",
        OAuthConfirmLinkView.as_view(),
        name="auth-oauth-confirm-link",
    ),
    path(
        "oauth/<str:provider>/authorize/",
        OAuthAuthorizeView.as_view(),
        name="auth-oauth-authorize",
    ),
    path(
        "oauth/<str:provider>/callback/",
        OAuthCallbackView.as_view(),
        name="auth-oauth-callback",
    ),
]
