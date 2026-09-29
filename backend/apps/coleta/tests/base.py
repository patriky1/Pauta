from datetime import datetime, timezone as tz
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.categories.models import Categoria
from apps.coleta.cliente import RespostaHttp
from apps.coleta.models import FonteNoticia

# data fixa "de agora" para os feeds de exemplo nao ficarem velhos com o tempo
AGORA = datetime(2026, 9, 29, 15, 0, tzinfo=tz.utc)


def resposta(conteudo=b"", **extras):
    return RespostaHttp(conteudo=conteudo, **extras)


@override_settings(COLETA_IDADE_MAXIMA_DIAS=3650)
class BaseColeta(TestCase):
    def setUp(self):
        cache.clear()
        self.brasil = Categoria.objects.create(nome="Brasil")
        self.politica = Categoria.objects.create(nome="Política", slug="politica")
        self.esportes = Categoria.objects.create(nome="Esportes")
        self.economia = Categoria.objects.create(nome="Economia")
        self.fonte = FonteNoticia.objects.create(
            nome="Agencia Exemplo", url_feed="https://exemplo.test/rss.xml",
            url_site="https://exemplo.test", categoria_padrao=self.brasil,
        )

    def baixar_por_url(self, mapa):
        """Substitui o download HTTP escolhendo a resposta pela URL da fonte
        (independe da ordem em que o banco devolve as fontes)."""
        def falso(url, *args, **kwargs):
            resultado = mapa[url]
            if isinstance(resultado, Exception):
                raise resultado
            return resultado

        return mock.patch("apps.coleta.services.baixar", side_effect=falso)

    def baixar_retornando(self, *respostas):
        """Substitui o download HTTP. Cada chamada devolve a proxima resposta da lista
        (ou levanta, se o item for uma excecao)."""
        return mock.patch("apps.coleta.services.baixar", side_effect=list(respostas))
