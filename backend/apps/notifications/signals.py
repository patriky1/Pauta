from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.comments.models import Comentario

from .services import notificar_resposta


@receiver(post_save, sender=Comentario)
def ao_criar_comentario(sender, instance, created, **kwargs):
    if created and instance.resposta_a_id:
        notificar_resposta(instance)
