from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.categories.models import Categoria, Tag
from apps.news.models import Noticia
from apps.users.models import User

from .models import AutorSeguido, CategoriaSeguida, Favorito, Historico, TagSeguida
from .serializers import FavoritoSerializer, HistoricoSerializer


class FavoritoViewSet(viewsets.ModelViewSet):
    serializer_class = FavoritoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        return Favorito.objects.filter(usuario=self.request.user).select_related(
            "noticia", "noticia__autor", "noticia__categoria"
        )

    def create(self, request, *args, **kwargs):
        noticia = get_object_or_404(Noticia, pk=request.data.get("noticia"))
        favorito, criado = Favorito.objects.get_or_create(
            usuario=request.user, noticia=noticia
        )
        if not criado:
            favorito.delete()
            return Response({"favoritada": False})
        from apps.analytics.models import Evento

        Evento.objects.create(tipo=Evento.Tipo.FAVORITO, noticia=noticia,
                              categoria=noticia.categoria, usuario=request.user)
        return Response({"favoritada": True}, status=status.HTTP_201_CREATED)


class HistoricoViewSet(viewsets.ModelViewSet):
    serializer_class = HistoricoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "delete", "head", "options"]

    def get_queryset(self):
        return Historico.objects.filter(usuario=self.request.user).select_related(
            "noticia", "noticia__autor", "noticia__categoria"
        )

    @action(detail=False, methods=["delete"])
    def limpar(self, request):
        self.get_queryset().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SeguirView(APIView):
    """Alterna o acompanhamento de categorias, autores e tags."""

    permission_classes = [IsAuthenticated]

    MAPA = {
        "categories": (CategoriaSeguida, Categoria, "categoria", "slug"),
        "authors": (AutorSeguido, User, "autor", "username"),
        "tags": (TagSeguida, Tag, "tag", "slug"),
    }

    def get(self, request, tipo):
        modelo, _, campo, _ = self._config(tipo)
        itens = modelo.objects.filter(usuario=request.user).select_related(campo)
        return Response(
            [
                {
                    "id": getattr(item, f"{campo}_id"),
                    "nome": getattr(getattr(item, campo), "nome", None),
                    "slug": getattr(getattr(item, campo), "slug",
                                    getattr(getattr(item, campo), "username", "")),
                }
                for item in itens
            ]
        )

    def post(self, request, tipo):
        modelo, alvo_modelo, campo, lookup = self._config(tipo)
        valor = request.data.get("valor") or request.data.get(lookup)
        alvo = get_object_or_404(alvo_modelo, **{lookup: valor})
        registro, criado = modelo.objects.get_or_create(
            usuario=request.user, **{campo: alvo}
        )
        if not criado:
            registro.delete()
        return Response({"seguindo": criado})

    def _config(self, tipo):
        if tipo not in self.MAPA:
            from rest_framework.exceptions import NotFound

            raise NotFound("Tipo invalido. Use categories, authors ou tags.")
        return self.MAPA[tipo]
