from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Count, Q, Sum
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.permissions import EhAdministrador

from .models import TipoUsuario, User
from .serializers import (
    AlterarSenhaSerializer,
    AutorSerializer,
    ConfirmarResetSerializer,
    LoginSerializer,
    PerfilUpdateSerializer,
    RegistroSerializer,
    SolicitarResetSerializer,
    UsuarioAdminSerializer,
    UsuarioSerializer,
)


class RegistroView(generics.CreateAPIView):
    serializer_class = RegistroSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        tokens = LoginSerializer.get_token(usuario)
        return Response(
            {
                "user": UsuarioSerializer(usuario, context={"request": request}).data,
                "access": str(tokens.access_token),
                "refresh": str(tokens),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"


class PerfilView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return PerfilUpdateSerializer
        return UsuarioSerializer

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(UsuarioSerializer(request.user, context={"request": request}).data)


class AlterarSenhaView(generics.GenericAPIView):
    serializer_class = AlterarSenhaSerializer
    permission_classes = [IsAuthenticated]
    throttle_scope = "auth"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Senha alterada."})


class SolicitarResetView(generics.GenericAPIView):
    serializer_class = SolicitarResetSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario, link = serializer.gerar_link(settings.SITE_URL)
        if usuario and link:
            send_mail(
                subject=f"{settings.SITE_NAME}: redefinicao de senha",
                message=(
                    f"Ola, {usuario.nome}.\n\n"
                    f"Use o link abaixo para criar uma nova senha:\n{link}\n\n"
                    "Se nao foi voce quem pediu, ignore esta mensagem."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[usuario.email],
                fail_silently=True,
            )
        # resposta neutra: nao revela se o e-mail existe
        return Response({"detail": "Se o e-mail existir, enviaremos as instrucoes."})


class ConfirmarResetView(generics.GenericAPIView):
    serializer_class = ConfirmarResetSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Senha redefinida. Voce ja pode entrar."})


class LogoutView(generics.GenericAPIView):
    """Logout e feito no cliente descartando os tokens; o endpoint existe para auditoria."""

    permission_classes = [IsAuthenticated]
    serializer_class = UsuarioSerializer

    def post(self, request):
        return Response({"detail": "Sessao encerrada."})


class AutorViewSet(viewsets.ReadOnlyModelViewSet):
    """Perfis publicos de quem escreve na plataforma."""

    serializer_class = AutorSerializer
    permission_classes = [AllowAny]
    lookup_field = "username"
    search_fields = ("nome", "username", "biografia")
    ordering_fields = ("nome", "total_noticias")
    ordering = ("-total_noticias",)

    def get_queryset(self):
        publicadas = Q(noticias__status="PUBLICADA")
        return (
            User.objects.redacao()
            .filter(is_active=True)
            .annotate(
                total_noticias=Count("noticias", filter=publicadas, distinct=True),
                total_visualizacoes=Sum("noticias__visualizacoes", filter=publicadas),
            )
            .filter(total_noticias__gt=0)
        )

    def get_serializer_context(self):
        contexto = super().get_serializer_context()
        if self.request.user.is_authenticated:
            from apps.interactions.models import AutorSeguido

            contexto["autores_seguidos"] = set(
                AutorSeguido.objects.filter(usuario=self.request.user).values_list(
                    "autor_id", flat=True
                )
            )
        return contexto

    @action(detail=True, methods=["get"], url_path="noticias")
    def noticias(self, request, username=None):
        from apps.news.models import Noticia
        from apps.news.serializers import NoticiaListaSerializer

        autor = self.get_object()
        consulta = Noticia.objects.publicadas().filter(autor=autor)
        pagina = self.paginate_queryset(consulta)
        serializer = NoticiaListaSerializer(pagina, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)


class UsuarioAdminViewSet(viewsets.ModelViewSet):
    """Gerenciamento de usuarios no painel administrativo."""

    serializer_class = UsuarioAdminSerializer
    permission_classes = [EhAdministrador]
    http_method_names = ["get", "patch", "post", "head", "options"]
    search_fields = ("nome", "username", "email")
    filterset_fields = ("tipo_usuario", "is_active")
    ordering_fields = ("date_joined", "nome")
    ordering = ("-date_joined",)
    queryset = User.objects.annotate(total_comentarios=Count("comentarios"))

    @action(detail=True, methods=["post"])
    def bloquear(self, request, pk=None):
        from django.utils import timezone

        usuario = self.get_object()
        if usuario == request.user:
            return Response(
                {"detail": "Voce nao pode bloquear a propria conta."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        usuario.is_active = False
        usuario.bloqueado_em = timezone.now()
        usuario.motivo_bloqueio = request.data.get("motivo", "")[:200]
        usuario.save(update_fields=["is_active", "bloqueado_em", "motivo_bloqueio"])
        return Response(self.get_serializer(usuario).data)

    @action(detail=True, methods=["post"])
    def desbloquear(self, request, pk=None):
        usuario = self.get_object()
        usuario.is_active = True
        usuario.bloqueado_em = None
        usuario.motivo_bloqueio = ""
        usuario.save(update_fields=["is_active", "bloqueado_em", "motivo_bloqueio"])
        return Response(self.get_serializer(usuario).data)

    @action(detail=True, methods=["post"], url_path="funcao")
    def alterar_funcao(self, request, pk=None):
        usuario = self.get_object()
        papel = request.data.get("tipo_usuario")
        if papel not in TipoUsuario.values:
            return Response(
                {"detail": "Funcao invalida.", "errors": {"tipo_usuario": TipoUsuario.values}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        usuario.tipo_usuario = papel
        usuario.is_staff = papel in {TipoUsuario.ADMIN, TipoUsuario.EDITOR}
        usuario.save(update_fields=["tipo_usuario", "is_staff"])
        return Response(self.get_serializer(usuario).data)
