from rest_framework import serializers

from .models import Notificacao


class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = ("id", "tipo", "titulo", "mensagem", "url", "lida", "criado_em")
        read_only_fields = fields
