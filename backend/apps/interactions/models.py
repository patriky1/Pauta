from django.conf import settings
from django.db import models
from django.utils import timezone


class Favorito(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="favoritos")
    noticia = models.ForeignKey("news.Noticia", on_delete=models.CASCADE,
                                related_name="favoritada_por")
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = ("usuario", "noticia")
        ordering = ["-criado_em"]
        verbose_name = "favorito"
        verbose_name_plural = "favoritos"


class Historico(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="historico")
    noticia = models.ForeignKey("news.Noticia", on_delete=models.CASCADE,
                                related_name="leituras")
    visto_em = models.DateTimeField(default=timezone.now, db_index=True)
    segundos_lidos = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("usuario", "noticia")
        ordering = ["-visto_em"]
        verbose_name = "item do historico"
        verbose_name_plural = "historico"


class CategoriaSeguida(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="categorias_seguidas")
    categoria = models.ForeignKey("categories.Categoria", on_delete=models.CASCADE,
                                  related_name="seguidores")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("usuario", "categoria")


class AutorSeguido(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="autores_seguidos")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name="seguidores")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("usuario", "autor")


class TagSeguida(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="tags_seguidas")
    tag = models.ForeignKey("categories.Tag", on_delete=models.CASCADE,
                            related_name="seguidores")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("usuario", "tag")
