from django.db.models import Count, F, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.categories.models import Categoria, Tag
from apps.categories.serializers import CategoriaSerializer, TagSerializer
from apps.core.pagination import PaginacaoCurta
from apps.core.permissions import EhAdministrador, EhAutorOuEditor, EhEquipeRedacao
from apps.users.models import User
from apps.users.serializers import AutorSerializer

from .filters import NoticiaFilter
from .models import (
    Anuncio,
    AtualizacaoAoVivo,
    CoberturaAoVivo,
    Noticia,
    StatusNoticia,
    Video,
)
from .serializers import (
    AnuncioSerializer,
    AtualizacaoAoVivoSerializer,
    CoberturaAoVivoSerializer,
    CoberturaResumoSerializer,
    NoticiaDetalheSerializer,
    NoticiaEscritaSerializer,
    NoticiaListaSerializer,
    VideoSerializer,
)
from .services import assuntos_em_alta, feed_para_voce, mais_lidas, registrar_leitura


class ContextoFavoritosMixin:
    """Marca no payload quais noticias o leitor ja salvou."""

    def get_serializer_context(self):
        contexto = super().get_serializer_context()
        usuario = self.request.user
        if usuario.is_authenticated:
            from apps.interactions.models import Favorito

            contexto["favoritos"] = set(
                Favorito.objects.filter(usuario=usuario).values_list("noticia_id", flat=True)
            )
        return contexto


class NoticiaViewSet(ContextoFavoritosMixin, viewsets.ReadOnlyModelViewSet):
    """Leitura publica das noticias publicadas."""

    permission_classes = [AllowAny]
    lookup_field = "slug"
    serializer_class = NoticiaListaSerializer
    filterset_class = NoticiaFilter
    search_fields = ("titulo", "subtitulo", "resumo", "conteudo")
    ordering_fields = ("data_publicacao", "visualizacoes", "titulo")
    ordering = ("-data_publicacao",)

    def get_queryset(self):
        return Noticia.objects.publicadas()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return NoticiaDetalheSerializer
        return NoticiaListaSerializer

    def retrieve(self, request, *args, **kwargs):
        noticia = self.get_object()
        registrar_leitura(request, noticia)
        noticia.refresh_from_db(fields=["visualizacoes"])
        serializer = self.get_serializer(noticia)
        return Response(serializer.data)

    def _pagina(self, consulta):
        pagina = self.paginate_queryset(consulta)
        serializer = NoticiaListaSerializer(pagina, many=True,
                                            context=self.get_serializer_context())
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"])
    def latest(self, request):
        return self._pagina(self.get_queryset().order_by("-data_publicacao"))

    @action(detail=False, methods=["get"], url_path="most-read")
    def most_read(self, request):
        periodo = request.query_params.get("periodo", "semana")
        return self._pagina(mais_lidas(self.get_queryset(), periodo))

    @action(detail=False, methods=["get"])
    def trending(self, request):
        dados = assuntos_em_alta()
        consulta = self.get_queryset()
        slugs = [item["slug"] for item in dados["categorias"][:5]]
        if slugs:
            consulta = consulta.filter(categoria__slug__in=slugs)
        destaques = consulta.order_by("-visualizacoes", "-data_publicacao")[:12]
        return Response(
            {
                "assuntos": dados["categorias"],
                "tags": dados["tags"],
                "noticias": NoticiaListaSerializer(
                    destaques, many=True, context=self.get_serializer_context()
                ).data,
            }
        )

    @action(detail=False, methods=["get"])
    def breaking(self, request):
        consulta = self.get_queryset().filter(breaking_news=True)[:5]
        return Response(
            NoticiaListaSerializer(
                consulta, many=True, context=self.get_serializer_context()
            ).data
        )

    @action(detail=False, methods=["get"])
    def destaques(self, request):
        """Composicao do hero: 1 manchete + secundarias."""
        consulta = self.get_queryset()
        principal = consulta.filter(destaque=True).first() or consulta.first()
        restantes = consulta.exclude(pk=principal.pk) if principal else consulta
        secundarias = list(restantes.filter(Q(destaque=True) | Q(exclusivo=True))[:4])
        if len(secundarias) < 4:
            secundarias = list(restantes[:4])
        contexto = self.get_serializer_context()
        return Response(
            {
                "principal": NoticiaDetalheSerializer(principal, context=contexto).data
                if principal else None,
                "secundarias": NoticiaListaSerializer(
                    secundarias, many=True, context=contexto
                ).data,
            }
        )

    @action(detail=False, methods=["get"], url_path="for-you")
    def for_you(self, request):
        return self._pagina(feed_para_voce(request.user, self.get_queryset()))

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def seguindo(self, request):
        from apps.interactions.models import AutorSeguido, CategoriaSeguida, TagSeguida

        usuario = request.user
        categorias = CategoriaSeguida.objects.filter(usuario=usuario).values_list(
            "categoria_id", flat=True)
        autores = AutorSeguido.objects.filter(usuario=usuario).values_list("autor_id", flat=True)
        tags = TagSeguida.objects.filter(usuario=usuario).values_list("tag_id", flat=True)
        consulta = self.get_queryset().filter(
            Q(categoria_id__in=categorias) | Q(autor_id__in=autores) | Q(tags__id__in=tags)
        ).distinct()
        return self._pagina(consulta)

    @action(detail=True, methods=["post"], permission_classes=[AllowAny],
            url_path="compartilhar")
    def compartilhar(self, request, slug=None):
        from apps.analytics.models import Evento
        from apps.core.utils import chave_sessao

        noticia = self.get_object()
        Evento.objects.create(
            tipo=Evento.Tipo.COMPARTILHAMENTO,
            noticia=noticia,
            categoria=noticia.categoria,
            usuario=request.user if request.user.is_authenticated else None,
            sessao=chave_sessao(request),
            rotulo=request.data.get("rede", "")[:40],
        )
        return Response({"detail": "Compartilhamento registrado."})

    @action(detail=True, methods=["post"], permission_classes=[AllowAny],
            url_path="tempo-leitura")
    def tempo_leitura_lido(self, request, slug=None):
        """Recebe do frontend quantos segundos o leitor ficou na materia."""
        from apps.analytics.models import Evento
        from apps.core.utils import chave_sessao

        noticia = self.get_object()
        try:
            segundos = max(0, min(int(request.data.get("segundos", 0)), 3600))
        except (TypeError, ValueError):
            return Response({"detail": "Valor invalido."},
                            status=status.HTTP_400_BAD_REQUEST)
        Evento.objects.create(
            tipo=Evento.Tipo.TEMPO_LEITURA,
            noticia=noticia,
            categoria=noticia.categoria,
            usuario=request.user if request.user.is_authenticated else None,
            sessao=chave_sessao(request),
            valor=segundos,
        )
        return Response({"detail": "Registrado."})


class NoticiaAdminViewSet(ContextoFavoritosMixin, viewsets.ModelViewSet):
    """CRUD editorial: rascunhos, agendamentos e arquivo."""

    permission_classes = [EhEquipeRedacao, EhAutorOuEditor]
    lookup_field = "slug"
    filterset_class = NoticiaFilter
    search_fields = ("titulo", "subtitulo", "resumo")
    ordering_fields = ("data_publicacao", "criado_em", "visualizacoes")
    ordering = ("-criado_em",)
    throttle_scope = "escrita"

    def get_queryset(self):
        consulta = Noticia.objects.all()
        usuario = self.request.user
        if usuario.is_authenticated and not usuario.e_editor:
            consulta = consulta.filter(autor=usuario)
        situacao = self.request.query_params.get("status")
        if situacao:
            consulta = consulta.filter(status=situacao.upper())
        return consulta

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return NoticiaDetalheSerializer
        return NoticiaEscritaSerializer

    def _mudar_status(self, request, novo):
        noticia = self.get_object()
        self.check_object_permissions(request, noticia)
        noticia.status = novo
        if novo == StatusNoticia.PUBLICADA and not noticia.data_publicacao:
            noticia.data_publicacao = timezone.now()
        noticia.save()
        if novo == StatusNoticia.PUBLICADA:
            from apps.notifications.services import notificar_publicacao

            notificar_publicacao(noticia)
        return Response(NoticiaDetalheSerializer(
            noticia, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def publicar(self, request, slug=None):
        return self._mudar_status(request, StatusNoticia.PUBLICADA)

    @action(detail=True, methods=["post"])
    def arquivar(self, request, slug=None):
        return self._mudar_status(request, StatusNoticia.ARQUIVADA)

    @action(detail=True, methods=["post"], url_path="revisao")
    def enviar_revisao(self, request, slug=None):
        return self._mudar_status(request, StatusNoticia.REVISAO)

    @action(detail=True, methods=["post"])
    def destacar(self, request, slug=None):
        noticia = self.get_object()
        noticia.destaque = not noticia.destaque
        noticia.save(update_fields=["destaque", "atualizado_em"])
        return Response({"destaque": noticia.destaque})

    @action(detail=True, methods=["post"], url_path="urgente")
    def marcar_urgente(self, request, slug=None):
        noticia = self.get_object()
        noticia.breaking_news = not noticia.breaking_news
        noticia.save(update_fields=["breaking_news", "atualizado_em"])
        if noticia.breaking_news and noticia.esta_publicada:
            from apps.notifications.services import notificar_urgente

            notificar_urgente(noticia)
        return Response({"breaking_news": noticia.breaking_news})


class CoberturaAoVivoViewSet(viewsets.ModelViewSet):
    permission_classes = [EhEquipeRedacao]
    lookup_field = "slug"
    serializer_class = CoberturaAoVivoSerializer
    ordering = ("-iniciada_em",)

    def get_queryset(self):
        consulta = CoberturaAoVivo.objects.select_related(
            "categoria", "criado_por"
        ).annotate(total_atualizacoes=Count("atualizacoes"))
        situacao = self.request.query_params.get("status")
        if situacao:
            consulta = consulta.filter(status=situacao.upper())
        return consulta

    def get_serializer_class(self):
        if self.action == "list":
            return CoberturaResumoSerializer
        return CoberturaAoVivoSerializer

    @action(detail=True, methods=["post"], url_path="atualizacoes")
    def adicionar_atualizacao(self, request, slug=None):
        cobertura = self.get_object()
        serializer = AtualizacaoAoVivoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        atualizacao = AtualizacaoAoVivo.objects.create(
            cobertura=cobertura,
            autor=request.user,
            titulo=serializer.validated_data.get("titulo", ""),
            conteudo=serializer.validated_data["conteudo"],
            importante=serializer.validated_data.get("importante", False),
        )
        return Response(
            AtualizacaoAoVivoSerializer(atualizacao).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"])
    def encerrar(self, request, slug=None):
        cobertura = self.get_object()
        cobertura.status = CoberturaAoVivo.Status.ENCERRADA
        cobertura.save()
        return Response(CoberturaAoVivoSerializer(cobertura).data)


class VideoViewSet(viewsets.ModelViewSet):
    serializer_class = VideoSerializer
    permission_classes = [EhEquipeRedacao]
    lookup_field = "slug"
    filterset_fields = ("categoria__slug", "plataforma")
    search_fields = ("titulo", "descricao")
    ordering = ("-publicado_em",)

    def get_queryset(self):
        consulta = Video.objects.select_related("categoria", "autor")
        if not (self.request.user.is_authenticated and self.request.user.e_redacao):
            consulta = consulta.filter(publicado=True)
        return consulta

    def retrieve(self, request, *args, **kwargs):
        video = self.get_object()
        Video.objects.filter(pk=video.pk).update(visualizacoes=F("visualizacoes") + 1)
        video.refresh_from_db(fields=["visualizacoes"])
        return Response(self.get_serializer(video).data)


class AnuncioViewSet(viewsets.ModelViewSet):
    serializer_class = AnuncioSerializer
    queryset = Anuncio.objects.all()
    filterset_fields = ("posicao", "ativo")

    def get_permissions(self):
        if self.action in ("list", "retrieve", "clique"):
            return [AllowAny()]
        return [EhAdministrador()]

    def get_queryset(self):
        consulta = Anuncio.objects.all()
        if not (self.request.user.is_authenticated and self.request.user.e_administrador):
            agora = timezone.now()
            consulta = consulta.filter(ativo=True, inicio__lte=agora).filter(
                Q(fim__isnull=True) | Q(fim__gte=agora)
            )
        return consulta

    @action(detail=True, methods=["post"], permission_classes=[AllowAny])
    def clique(self, request, pk=None):
        Anuncio.objects.filter(pk=pk).update(cliques=F("cliques") + 1)
        return Response({"detail": "Clique registrado."})


class BuscaView(APIView):
    """Busca unificada: noticias, autores, categorias e tags."""

    permission_classes = [AllowAny]
    throttle_scope = "busca"

    def get(self, request):
        termo = (request.query_params.get("q") or "").strip()
        if len(termo) < 2:
            return Response(
                {"noticias": [], "autores": [], "categorias": [], "tags": [], "total": 0}
            )

        contexto = {"request": request}
        if request.user.is_authenticated:
            from apps.interactions.models import Favorito

            contexto["favoritos"] = set(
                Favorito.objects.filter(usuario=request.user).values_list(
                    "noticia_id", flat=True)
            )

        noticias = Noticia.objects.publicadas().filter(
            Q(titulo__icontains=termo)
            | Q(subtitulo__icontains=termo)
            | Q(resumo__icontains=termo)
            | Q(conteudo__icontains=termo)
            | Q(tags__nome__icontains=termo)
        ).distinct()

        filtros = {
            "categoria": "categoria__slug",
            "autor": "autor__username",
            "tag": "tags__slug",
        }
        for parametro, campo in filtros.items():
            valor = request.query_params.get(parametro)
            if valor:
                noticias = noticias.filter(**{campo: valor})
        desde = request.query_params.get("desde")
        if desde:
            noticias = noticias.filter(data_publicacao__gte=desde)
        ate = request.query_params.get("ate")
        if ate:
            noticias = noticias.filter(data_publicacao__lte=ate)

        paginador = PaginacaoCurta()
        pagina = paginador.paginate_queryset(noticias, request, view=self)

        autores = User.objects.redacao().filter(
            Q(nome__icontains=termo) | Q(username__icontains=termo)
        ).annotate(total_noticias=Count("noticias", filter=Q(noticias__status="PUBLICADA")))[:5]
        categorias = Categoria.objects.filter(nome__icontains=termo, ativa=True)[:5]
        tags = Tag.objects.filter(nome__icontains=termo)[:8]

        return Response(
            {
                "termo": termo,
                "total": noticias.count(),
                "noticias": NoticiaListaSerializer(pagina, many=True, context=contexto).data,
                "proxima_pagina": paginador.get_next_link(),
                "autores": AutorSerializer(autores, many=True, context=contexto).data,
                "categorias": CategoriaSerializer(categorias, many=True,
                                                  context=contexto).data,
                "tags": TagSerializer(tags, many=True).data,
            }
        )
