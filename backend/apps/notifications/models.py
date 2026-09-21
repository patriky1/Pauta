from django.conf import settings
from django.db import models


class Notificacao(models.Model):
    class Tipo(models.TextChoices):
        PUBLICACAO = "PUBLICACAO", "Nova noticia"
        CATEGORIA = "CATEGORIA", "Noticia de uma categoria seguida"
        AUTOR = "AUTOR", "Noticia de um autor seguido"
        URGENTE = "URGENTE", "Noticia urgente"
        RESPOSTA = "RESPOSTA", "Resposta ao seu comentario"
        SISTEMA = "SISTEMA", "Aviso do sistema"

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="notificacoes")
    tipo = models.CharField(max_length=12, choices=Tipo.choices, default=Tipo.SISTEMA)
    titulo = models.CharField(max_length=160)
    mensagem = models.CharField(max_length=300, blank=True)
    url = models.CharField(max_length=300, blank=True)
    lida = models.BooleanField(default=False, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "notificacao"
        verbose_name_plural = "notificacoes"

    def __str__(self):
        return f"{self.titulo} -> {self.usuario}"
