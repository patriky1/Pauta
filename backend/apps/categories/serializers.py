from rest_framework import serializers

from .models import Categoria, Tag


class CategoriaSerializer(serializers.ModelSerializer):
    total_noticias = serializers.IntegerField(read_only=True, default=0)
    seguindo = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = ("id", "nome", "slug", "descricao", "cor", "ordem",
                  "ativa", "total_noticias", "seguindo")
        read_only_fields = ("id", "slug", "total_noticias", "seguindo")

    def get_seguindo(self, obj):
        seguidas = self.context.get("categorias_seguidas")
        if seguidas is None:
            return False
        return obj.pk in seguidas


class CategoriaResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ("id", "nome", "slug", "cor")
        read_only_fields = fields


class TagSerializer(serializers.ModelSerializer):
    total_noticias = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Tag
        fields = ("id", "nome", "slug", "total_noticias")
        read_only_fields = ("id", "slug", "total_noticias")
