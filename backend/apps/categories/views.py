from django.db.models import Count, Q
from rest_framework import viewsets

from apps.core.permissions import EhEquipeRedacao

from .models import Categoria, Tag
from .serializers import CategoriaSerializer, TagSerializer

PUBLICADAS = Q(noticias__status="PUBLICADA")


class CategoriaViewSet(viewsets.ModelViewSet):
    serializer_class = CategoriaSerializer
    permission_classes = [EhEquipeRedacao]
    lookup_field = "slug"
    pagination_class = None
    search_fields = ("nome", "descricao")
    ordering_fields = ("ordem", "nome", "total_noticias")

    def get_queryset(self):
        consulta = Categoria.objects.annotate(
            total_noticias=Count("noticias", filter=PUBLICADAS, distinct=True)
        )
        if self.request.query_params.get("todas") != "1":
            consulta = consulta.filter(ativa=True)
        return consulta

    def get_serializer_context(self):
        contexto = super().get_serializer_context()
        if self.request.user.is_authenticated:
            from apps.interactions.models import CategoriaSeguida

            contexto["categorias_seguidas"] = set(
                CategoriaSeguida.objects.filter(usuario=self.request.user).values_list(
                    "categoria_id", flat=True
                )
            )
        return contexto


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [EhEquipeRedacao]
    lookup_field = "slug"
    search_fields = ("nome",)
    ordering_fields = ("nome", "total_noticias")
    ordering = ("-total_noticias",)
    queryset = Tag.objects.annotate(
        total_noticias=Count("noticias", filter=PUBLICADAS, distinct=True)
    )
