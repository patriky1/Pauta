from datetime import timedelta

from django.db.models import Avg, Count, Sum
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.categories.models import Categoria
from apps.comments.models import Comentario, Denuncia
from apps.core.permissions import EhEquipeRedacao
from apps.core.utils import chave_sessao
from apps.news.models import Noticia, StatusNoticia
from apps.news.serializers import NoticiaListaSerializer
from apps.news.services import assuntos_em_alta, resumo_audiencia
from apps.users.models import User

from .models import Evento


class RegistrarEventoView(APIView):
    """Endpoint publico usado pelo frontend para cliques e compartilhamentos."""

    permission_classes = [AllowAny]

    def post(self, request):
        tipo = request.data.get("tipo", Evento.Tipo.CLIQUE)
        if tipo not in Evento.Tipo.values:
            return Response({"detail": "Tipo de evento invalido."}, status=400)
        noticia = None
        slug = request.data.get("noticia")
        if slug:
            noticia = Noticia.objects.filter(slug=slug).first()
        Evento.objects.create(
            tipo=tipo,
            noticia=noticia,
            categoria=noticia.categoria if noticia else None,
            usuario=request.user if request.user.is_authenticated else None,
            sessao=chave_sessao(request),
            rotulo=str(request.data.get("rotulo", ""))[:40],
            valor=int(request.data.get("valor", 0) or 0),
        )
        return Response({"detail": "ok"})


class TendenciasView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(assuntos_em_alta(limite=10))


class PainelView(APIView):
    """Numeros do painel administrativo."""

    permission_classes = [EhEquipeRedacao]

    def get(self, request):
        agora = timezone.now()
        ultimos_30 = agora - timedelta(days=30)
        eventos = Evento.objects.filter(criado_em__gte=ultimos_30)

        top_noticias = Noticia.objects.publicadas().order_by("-visualizacoes")[:8]
        top_categorias = (
            Categoria.objects.annotate(
                total=Count("eventos", filter=None, distinct=False)
            ).order_by("-total")[:8]
        )

        tempo_medio = eventos.filter(tipo=Evento.Tipo.TEMPO_LEITURA).aggregate(
            media=Avg("valor"))["media"] or 0

        return Response(
            {
                "totais": {
                    "noticias": Noticia.objects.count(),
                    "publicadas": Noticia.objects.filter(
                        status=StatusNoticia.PUBLICADA).count(),
                    "rascunhos": Noticia.objects.filter(
                        status=StatusNoticia.RASCUNHO).count(),
                    "usuarios": User.objects.count(),
                    "autores": User.objects.redacao().count(),
                    "comentarios": Comentario.objects.count(),
                    "comentarios_pendentes": Comentario.objects.filter(
                        status=Comentario.Status.PENDENTE).count(),
                    "denuncias_abertas": Denuncia.objects.filter(
                        status=Denuncia.Status.ABERTA).count(),
                    "usuarios_bloqueados": User.objects.filter(is_active=False).count(),
                    "visualizacoes": Noticia.objects.aggregate(
                        total=Sum("visualizacoes"))["total"] or 0,
                    "tempo_medio_leitura": round(tempo_medio),
                },
                "eventos_por_tipo": list(
                    eventos.values("tipo").annotate(total=Count("id")).order_by("-total")
                ),
                "serie": resumo_audiencia(dias=14),
                "top_noticias": NoticiaListaSerializer(
                    top_noticias, many=True, context={"request": request}).data,
                "top_categorias": [
                    {"nome": c.nome, "slug": c.slug, "cor": c.cor, "total": c.total}
                    for c in top_categorias
                ],
            }
        )
