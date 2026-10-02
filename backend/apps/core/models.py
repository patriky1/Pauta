from django.db import models


class ModeloBase(models.Model):
    """Campos de auditoria reutilizados por todos os models do projeto."""

    criado_em = models.DateTimeField("criado em", auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        abstract = True
