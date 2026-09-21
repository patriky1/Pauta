from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import (
    AlterarSenhaView,
    ConfirmarResetView,
    LoginView,
    LogoutView,
    PerfilView,
    RegistroView,
    SolicitarResetView,
)

urlpatterns = [
    path("register/", RegistroView.as_view(), name="auth-registro"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("verify/", TokenVerifyView.as_view(), name="auth-verify"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", PerfilView.as_view(), name="auth-perfil"),
    path("password/change/", AlterarSenhaView.as_view(), name="auth-alterar-senha"),
    path("password/reset/", SolicitarResetView.as_view(), name="auth-reset"),
    path("password/reset/confirm/", ConfirmarResetView.as_view(), name="auth-reset-confirma"),
]
