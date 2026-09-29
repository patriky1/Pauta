from django.conf import settings
from django.db import models


class Evento(models.Model):
    """Registro bruto de audiencia. Alimenta tendencias, mais lidas e o painel."""

    class Tipo(models.TextChoices):
        VISUALIZACAO = "VIEW", "Visualizacao"
        CLIQUE = "CLICK", "Clique"
        COMPARTILHAMENTO = "SHARE", "Compartilhamento"
        FAVORITO = "FAVORITE", "Favorito"
        TEMPO_LEITURA = "READ_TIME", "Tempo de leitura"

    tipo = models.CharField(max_length=10, choices=Tipo.choices, db_index=True)
    noticia = models.ForeignKey("news.Noticia", on_delete=models.CASCADE, blank=True,
                                null=True, related_name="eventos")
    categoria = models.ForeignKey("categories.Categoria", on_delete=models.SET_NULL,
                                  blank=True, null=True, related_name="eventos")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                blank=True, null=True, related_name="eventos")
    sessao = models.CharField(max_length=64, blank=True, db_index=True)
    rotulo = models.CharField(max_length=40, blank=True)
    valor = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "evento"
        verbose_name_plural = "eventos"
        ordering = ["-criado_em"]
        indexes = [models.Index(fields=["tipo", "-criado_em"])]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.criado_em:%d/%m %H:%M}"
