from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UsuarioManager


class TipoUsuario(models.TextChoices):
    ADMIN = "ADMIN", "Administrador"
    EDITOR = "EDITOR", "Editor"
    JORNALISTA = "JORNALISTA", "Jornalista"
    AUTOR = "AUTOR", "Autor"
    USUARIO = "USUARIO", "Usuario"


PAPEIS_REDACAO = [
    TipoUsuario.ADMIN,
    TipoUsuario.EDITOR,
    TipoUsuario.JORNALISTA,
    TipoUsuario.AUTOR,
]


class User(AbstractUser):
    """Usuario da plataforma: leitor, autor, jornalista, editor ou administrador."""

    first_name = None
    last_name = None

    nome = models.CharField("nome", max_length=150)
    email = models.EmailField("e-mail", unique=True)
    foto = models.ImageField("foto", upload_to="usuarios/", blank=True, null=True)
    biografia = models.TextField("biografia", blank=True)
    tipo_usuario = models.CharField(
        "tipo de usuario",
        max_length=12,
        choices=TipoUsuario.choices,
        default=TipoUsuario.USUARIO,
        db_index=True,
    )
    # redes sociais exibidas no perfil publico do autor
    site = models.URLField("site", blank=True)
    twitter = models.CharField("twitter/X", max_length=60, blank=True)
    instagram = models.CharField("instagram", max_length=60, blank=True)
    linkedin = models.CharField("linkedin", max_length=120, blank=True)

    bloqueado_em = models.DateTimeField("bloqueado em", blank=True, null=True)
    motivo_bloqueio = models.CharField("motivo do bloqueio", max_length=200, blank=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "nome"]

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} (@{self.username})"

    def save(self, *args, **kwargs):
        if not self.nome:
            self.nome = self.username
        super().save(*args, **kwargs)

    @property
    def data_cadastro(self):
        return self.date_joined

    @property
    def ativo(self):
        return self.is_active

    @property
    def e_redacao(self):
        return self.is_superuser or self.tipo_usuario in PAPEIS_REDACAO

    @property
    def e_administrador(self):
        return self.is_superuser or self.tipo_usuario == TipoUsuario.ADMIN

    @property
    def e_editor(self):
        return self.is_superuser or self.tipo_usuario in {
            TipoUsuario.ADMIN,
            TipoUsuario.EDITOR,
        }
