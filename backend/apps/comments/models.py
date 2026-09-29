from django.conf import settings
from django.db import models

from apps.core.models import ModeloBase


class Comentario(ModeloBase):
    class Status(models.TextChoices):
        PUBLICADO = "PUBLICADO", "Publicado"
        PENDENTE = "PENDENTE", "Aguardando moderacao"
        OCULTO = "OCULTO", "Oculto"
        REMOVIDO = "REMOVIDO", "Removido"

    noticia = models.ForeignKey(
        "news.Noticia", on_delete=models.CASCADE, related_name="comentarios"
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comentarios"
    )
    resposta_a = models.ForeignKey(
        "self", on_delete=models.CASCADE, blank=True, null=True, related_name="respostas"
    )
    conteudo = models.TextField("comentario", max_length=2000)
    status = models.CharField("status", max_length=10, choices=Status.choices,
                              default=Status.PUBLICADO, db_index=True)
    editado = models.BooleanField("editado", default=False)

    class Meta:
        verbose_name = "comentario"
        verbose_name_plural = "comentarios"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.autor} em {self.noticia}"

    @property
    def total_curtidas(self):
        return self.curtidas.count()


class CurtidaComentario(models.Model):
    comentario = models.ForeignKey(
        Comentario, on_delete=models.CASCADE, related_name="curtidas"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="curtidas"
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("comentario", "usuario")
        verbose_name = "curtida"
        verbose_name_plural = "curtidas"


class Denuncia(ModeloBase):
    class Motivo(models.TextChoices):
        SPAM = "SPAM", "Spam"
        OFENSIVO = "OFENSIVO", "Conteudo ofensivo"
        DESINFORMACAO = "DESINFORMACAO", "Desinformacao"
        OUTRO = "OUTRO", "Outro"

    class Status(models.TextChoices):
        ABERTA = "ABERTA", "Aberta"
        RESOLVIDA = "RESOLVIDA", "Resolvida"
        DESCARTADA = "DESCARTADA", "Descartada"

    comentario = models.ForeignKey(
        Comentario, on_delete=models.CASCADE, related_name="denuncias"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="denuncias"
    )
    motivo = models.CharField(max_length=14, choices=Motivo.choices)
    descricao = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ABERTA)

    class Meta:
        verbose_name = "denuncia"
        verbose_name_plural = "denuncias"
        unique_together = ("comentario", "usuario")
        ordering = ["-criado_em"]
