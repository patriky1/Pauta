"""Regras de recomendacao, tendencias e contagem de leitura."""
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Case, Count, F, FloatField, IntegerField, Value, When
from django.db.models.functions import TruncDate
from django.utils import timezone

PESO_CATEGORIA = 40
PESO_AUTOR = 30
PESO_TAG = 20
PESO_DESTAQUE = 10
PESO_URGENTE = 25
JANELA_RECENCIA_HORAS = 72


def _interesses(usuario):
    """Coleta o que o usuario segue e o que ja consumiu."""
    from apps.interactions.models import AutorSeguido, CategoriaSeguida, Historico, TagSeguida

    return {
        "categorias": set(
            CategoriaSeguida.objects.filter(usuario=usuario).values_list("categoria_id", flat=True)
        ),
        "autores": set(
            AutorSeguido.objects.filter(usuario=usuario).values_list("autor_id", flat=True)
        ),
        "tags": set(TagSeguida.objects.filter(usuario=usuario).values_list("tag_id", flat=True)),
        "lidas": set(
            Historico.objects.filter(usuario=usuario)
            .order_by("-visto_em")
            .values_list("noticia_id", flat=True)[:200]
        ),
    }


def feed_para_voce(usuario, consulta):
    """Ordena as noticias por afinidade com o perfil do leitor.

    Pontuacao = interesses declarados + recencia + popularidade.
    A arquitetura permite trocar esta funcao por um servico de IA sem alterar a view.
    """
    if not usuario or not usuario.is_authenticated:
        return feed_popular(consulta)

    perfil = _interesses(usuario)
    if not (perfil["categorias"] or perfil["autores"] or perfil["tags"]):
        return feed_popular(consulta)

    limite_recente = timezone.now() - timedelta(hours=JANELA_RECENCIA_HORAS)

    return (
        consulta.annotate(
            pontos_categoria=Case(
                When(categoria_id__in=perfil["categorias"], then=Value(PESO_CATEGORIA)),
                default=Value(0), output_field=IntegerField(),
            ),
            pontos_autor=Case(
                When(autor_id__in=perfil["autores"], then=Value(PESO_AUTOR)),
                default=Value(0), output_field=IntegerField(),
            ),
            pontos_tag=Case(
                When(tags__id__in=perfil["tags"], then=Value(PESO_TAG)),
                default=Value(0), output_field=IntegerField(),
            ),
            pontos_recencia=Case(
                When(data_publicacao__gte=limite_recente, then=Value(15)),
                default=Value(0), output_field=IntegerField(),
            ),
            pontos_destaque=Case(
                When(destaque=True, then=Value(PESO_DESTAQUE)),
                default=Value(0), output_field=IntegerField(),
            ),
            pontos_urgente=Case(
                When(breaking_news=True, then=Value(PESO_URGENTE)),
                default=Value(0), output_field=IntegerField(),
            ),
            ja_lida=Case(
                When(id__in=perfil["lidas"], then=Value(-35)),
                default=Value(0), output_field=IntegerField(),
            ),
            relevancia=(
                F("pontos_categoria") + F("pontos_autor") + F("pontos_tag")
                + F("pontos_recencia") + F("pontos_destaque") + F("pontos_urgente")
                + F("ja_lida") + F("visualizacoes") * Value(0.01, output_field=FloatField())
            ),
        )
        .distinct()
        .order_by("-relevancia", "-data_publicacao")
    )


def feed_popular(consulta):
    """Fallback para visitantes: mistura relevancia editorial e audiencia."""
    limite = timezone.now() - timedelta(days=3)
    return consulta.annotate(
        relevancia=(
            Case(When(destaque=True, then=Value(20)), default=Value(0),
                 output_field=IntegerField())
            + Case(When(breaking_news=True, then=Value(30)), default=Value(0),
                   output_field=IntegerField())
            + Case(When(data_publicacao__gte=limite, then=Value(15)), default=Value(0),
                   output_field=IntegerField())
            + F("visualizacoes") * Value(0.02, output_field=FloatField())
        )
    ).order_by("-relevancia", "-data_publicacao")


def periodo_para_data(periodo):
    agora = timezone.now()
    return {
        "hoje": agora - timedelta(days=1),
        "semana": agora - timedelta(days=7),
        "mes": agora - timedelta(days=30),
    }.get(periodo, agora - timedelta(days=7))


def assuntos_em_alta(limite=10, horas=48):
    """Ranking de assuntos calculado a partir dos eventos reais de leitura."""
    from apps.analytics.models import Evento

    chave = f"tendencias:{limite}:{horas}"
    resultado = cache.get(chave)
    if resultado is not None:
        return resultado

    desde = timezone.now() - timedelta(hours=horas)
    base = Evento.objects.filter(tipo=Evento.Tipo.VISUALIZACAO, criado_em__gte=desde)

    categorias = (
        base.filter(noticia__isnull=False)
        .values("noticia__categoria__nome", "noticia__categoria__slug",
                "noticia__categoria__cor")
        .annotate(total=Count("id"))
        .order_by("-total")[:limite]
    )
    tags = (
        base.filter(noticia__isnull=False)
        .values("noticia__tags__nome", "noticia__tags__slug")
        .annotate(total=Count("id"))
        .order_by("-total")[:limite]
    )

    resultado = {
        "categorias": [
            {
                "nome": item["noticia__categoria__nome"],
                "slug": item["noticia__categoria__slug"],
                "cor": item["noticia__categoria__cor"],
                "total": item["total"],
            }
            for item in categorias
            if item["noticia__categoria__slug"]
        ],
        "tags": [
            {
                "nome": item["noticia__tags__nome"],
                "slug": item["noticia__tags__slug"],
                "total": item["total"],
            }
            for item in tags
            if item["noticia__tags__slug"]
        ],
    }
    cache.set(chave, resultado, 300)
    return resultado


def registrar_leitura(request, noticia):
    """Conta a visualizacao uma vez por sessao a cada 6 horas."""
    from apps.analytics.models import Evento
    from apps.core.utils import chave_sessao
    from apps.interactions.models import Historico
    from apps.news.models import Noticia

    sessao = chave_sessao(request)
    chave = f"leitura:{sessao}:{noticia.pk}"
    if cache.get(chave):
        return False

    cache.set(chave, True, 60 * 60 * 6)
    Noticia.objects.filter(pk=noticia.pk).update(visualizacoes=F("visualizacoes") + 1)
    Evento.objects.create(
        tipo=Evento.Tipo.VISUALIZACAO,
        noticia=noticia,
        categoria=noticia.categoria,
        usuario=request.user if request.user.is_authenticated else None,
        sessao=sessao,
    )
    if request.user.is_authenticated:
        Historico.objects.update_or_create(
            usuario=request.user, noticia=noticia,
            defaults={"visto_em": timezone.now()},
        )
    return True


def total_visualizacoes_periodo(periodo="semana"):
    from apps.analytics.models import Evento

    return Evento.objects.filter(
        tipo=Evento.Tipo.VISUALIZACAO, criado_em__gte=periodo_para_data(periodo)
    ).aggregate(total=Count("id"))["total"] or 0


def mais_lidas(consulta, periodo="semana"):
    """Ranking por leituras registradas no periodo; cai para o total historico se vazio."""
    from apps.analytics.models import Evento

    desde = periodo_para_data(periodo)
    ids = (
        Evento.objects.filter(tipo=Evento.Tipo.VISUALIZACAO, criado_em__gte=desde,
                              noticia__isnull=False)
        .values("noticia_id")
        .annotate(total=Count("id"))
        .order_by("-total")
        .values_list("noticia_id", flat=True)[:30]
    )
    ids = list(ids)
    if not ids:
        return consulta.order_by("-visualizacoes", "-data_publicacao")

    ordem = Case(*[When(pk=pk, then=Value(pos)) for pos, pk in enumerate(ids)],
                 output_field=IntegerField())
    return consulta.filter(pk__in=ids).annotate(posicao=ordem).order_by("posicao")


def resumo_audiencia(dias=14):
    """Serie diaria de visualizacoes para o grafico do painel."""
    from apps.analytics.models import Evento

    desde = timezone.now() - timedelta(days=dias)
    dados = (
        Evento.objects.filter(criado_em__gte=desde)
        .annotate(dia=TruncDate("criado_em"))
        .values("dia", "tipo")
        .annotate(total=Count("id"))
        .order_by("dia")
    )
    serie = {}
    for linha in dados:
        dia = linha["dia"].isoformat() if linha["dia"] else ""
        entrada = serie.setdefault(dia, {"dia": dia, "visualizacoes": 0, "interacoes": 0})
        if linha["tipo"] == Evento.Tipo.VISUALIZACAO:
            entrada["visualizacoes"] += linha["total"]
        else:
            entrada["interacoes"] += linha["total"]
    return list(serie.values())
