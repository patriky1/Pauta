from rest_framework import serializers

from apps.news.serializers import NoticiaListaSerializer

from .models import Favorito, Historico


class FavoritoSerializer(serializers.ModelSerializer):
    noticia = NoticiaListaSerializer(read_only=True)

    class Meta:
        model = Favorito
        fields = ("id", "noticia", "criado_em")


class HistoricoSerializer(serializers.ModelSerializer):
    noticia = NoticiaListaSerializer(read_only=True)

    class Meta:
        model = Historico
        fields = ("id", "noticia", "visto_em", "segundos_lidos")
