from django.db import models

from apps.core.models import ModeloBase
from apps.core.utils import slug_unico


class Categoria(ModeloBase):
    nome = models.CharField("nome", max_length=60, unique=True)
    slug = models.SlugField("slug", max_length=70, unique=True, blank=True)
    descricao = models.CharField("descricao", max_length=200, blank=True)
    cor = models.CharField("cor (hex)", max_length=7, default="#1B48C4")
    ordem = models.PositiveSmallIntegerField("ordem no menu", default=0)
    ativa = models.BooleanField("ativa", default=True)

    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorias"
        ordering = ["ordem", "nome"]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slug_unico(Categoria, self.nome, self)
        super().save(*args, **kwargs)


class Tag(ModeloBase):
    nome = models.CharField("nome", max_length=50, unique=True)
    slug = models.SlugField("slug", max_length=60, unique=True, blank=True)

    class Meta:
        verbose_name = "tag"
        verbose_name_plural = "tags"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slug_unico(Tag, self.nome, self)
        super().save(*args, **kwargs)
