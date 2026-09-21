from django.contrib.auth import password_validation
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import TipoUsuario, User


class UsuarioResumoSerializer(serializers.ModelSerializer):
    """Usado dentro de noticias, comentarios e listagens."""

    class Meta:
        model = User
        fields = ("id", "nome", "username", "foto", "tipo_usuario")
        read_only_fields = fields


class UsuarioSerializer(serializers.ModelSerializer):
    data_cadastro = serializers.DateTimeField(source="date_joined", read_only=True)
    ativo = serializers.BooleanField(source="is_active", read_only=True)

    class Meta:
        model = User
        fields = (
            "id", "nome", "username", "email", "foto", "biografia", "tipo_usuario",
            "site", "twitter", "instagram", "linkedin", "data_cadastro", "ativo",
        )
        read_only_fields = ("id", "tipo_usuario", "data_cadastro", "ativo")


class PerfilUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("nome", "email", "foto", "biografia", "site",
                  "twitter", "instagram", "linkedin")

    def validate_email(self, valor):
        consulta = User.objects.filter(email__iexact=valor)
        if self.instance:
            consulta = consulta.exclude(pk=self.instance.pk)
        if consulta.exists():
            raise serializers.ValidationError("Este e-mail ja esta em uso.")
        return valor.lower()


class AutorSerializer(serializers.ModelSerializer):
    """Perfil publico do autor."""

    total_noticias = serializers.IntegerField(read_only=True, default=0)
    total_visualizacoes = serializers.IntegerField(read_only=True, default=0)
    seguindo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "nome", "username", "foto", "biografia", "tipo_usuario",
            "site", "twitter", "instagram", "linkedin",
            "total_noticias", "total_visualizacoes", "seguindo",
        )

    def get_seguindo(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        cache = self.context.get("autores_seguidos")
        if cache is not None:
            return obj.pk in cache
        return obj.seguidores.filter(usuario=request.user).exists()


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("id", "nome", "username", "email", "password", "password_confirm")

    def validate_username(self, valor):
        if User.objects.filter(username__iexact=valor).exists():
            raise serializers.ValidationError("Este nome de usuario ja existe.")
        return valor

    def validate_email(self, valor):
        if User.objects.filter(email__iexact=valor).exists():
            raise serializers.ValidationError("Este e-mail ja esta cadastrado.")
        return valor.lower()

    def validate(self, dados):
        if dados["password"] != dados.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "As senhas nao conferem."})
        password_validation.validate_password(dados["password"])
        return dados

    def create(self, dados):
        return User.objects.create_user(
            username=dados["username"],
            email=dados["email"],
            password=dados["password"],
            nome=dados.get("nome") or dados["username"],
            tipo_usuario=TipoUsuario.USUARIO,
        )


class LoginSerializer(TokenObtainPairSerializer):
    """Aceita username ou e-mail no campo `username` e devolve o usuario junto."""

    def validate(self, attrs):
        login = attrs.get(self.username_field, "")
        if "@" in login:
            usuario = User.objects.filter(email__iexact=login).first()
            if usuario:
                attrs[self.username_field] = usuario.username
        dados = super().validate(attrs)
        if not self.user.is_active:
            raise serializers.ValidationError("Esta conta esta bloqueada.")
        dados["user"] = UsuarioSerializer(self.user, context=self.context).data
        return dados


class AlterarSenhaSerializer(serializers.Serializer):
    senha_atual = serializers.CharField(write_only=True)
    nova_senha = serializers.CharField(write_only=True)

    def validate_senha_atual(self, valor):
        if not self.context["request"].user.check_password(valor):
            raise serializers.ValidationError("Senha atual incorreta.")
        return valor

    def validate_nova_senha(self, valor):
        password_validation.validate_password(valor, self.context["request"].user)
        return valor

    def save(self, **kwargs):
        usuario = self.context["request"].user
        usuario.set_password(self.validated_data["nova_senha"])
        usuario.save(update_fields=["password"])
        return usuario


class SolicitarResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def gerar_link(self, base_url):
        usuario = User.objects.filter(email__iexact=self.validated_data["email"]).first()
        if not usuario:
            return None, None
        uid = urlsafe_base64_encode(force_bytes(usuario.pk))
        token = default_token_generator.make_token(usuario)
        return usuario, f"{base_url}/redefinir-senha?uid={uid}&token={token}"


class ConfirmarResetSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    nova_senha = serializers.CharField(write_only=True)

    def validate(self, dados):
        try:
            pk = force_str(urlsafe_base64_decode(dados["uid"]))
            usuario = User.objects.get(pk=pk)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            raise serializers.ValidationError({"uid": "Link invalido."})
        if not default_token_generator.check_token(usuario, dados["token"]):
            raise serializers.ValidationError({"token": "Link expirado. Peca um novo."})
        password_validation.validate_password(dados["nova_senha"], usuario)
        dados["usuario"] = usuario
        return dados

    def save(self, **kwargs):
        usuario = self.validated_data["usuario"]
        usuario.set_password(self.validated_data["nova_senha"])
        usuario.save(update_fields=["password"])
        return usuario


class UsuarioAdminSerializer(serializers.ModelSerializer):
    """Listagem/edicao de usuarios no painel administrativo."""

    total_comentarios = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = User
        fields = (
            "id", "nome", "username", "email", "foto", "tipo_usuario",
            "is_active", "date_joined", "last_login", "motivo_bloqueio",
            "total_comentarios",
        )
        read_only_fields = ("id", "username", "email", "date_joined", "last_login")
