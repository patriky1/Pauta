from django_filters import rest_framework as filters

from .models import Noticia


class NoticiaFilter(filters.FilterSet):
    categoria = filters.CharFilter(field_name="categoria__slug", lookup_expr="iexact")
    tag = filters.CharFilter(field_name="tags__slug", lookup_expr="iexact")
    autor = filters.CharFilter(field_name="autor__username", lookup_expr="iexact")
    desde = filters.DateTimeFilter(field_name="data_publicacao", lookup_expr="gte")
    ate = filters.DateTimeFilter(field_name="data_publicacao", lookup_expr="lte")
    formato = filters.CharFilter(field_name="formato", lookup_expr="iexact")
    destaque = filters.BooleanFilter(field_name="destaque")
    exclusivo = filters.BooleanFilter(field_name="exclusivo")

    class Meta:
        model = Noticia
        fields = ["categoria", "tag", "autor", "desde", "ate",
                  "formato", "destaque", "exclusivo"]
