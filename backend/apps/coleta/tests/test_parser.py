"""Testes da logica pura (parser, sanitizacao, deduplicacao e categorizacao).

Nao dependem do banco: rodam no `python manage.py test` e tambem isolados com
`python -m unittest apps.coleta.tests.test_parser` a partir da pasta backend/.
"""
import unittest
from datetime import datetime, timezone

from apps.coleta import parser
from apps.coleta.categorizacao import Categorizador
from apps.coleta.texto import (
    gerar_hash,
    imagem_util,
    normalizar_texto,
    normalizar_url,
    resumir,
    sanitizar_html,
    texto_limpo,
    url_segura,
)

from . import amostras


class ParserTests(unittest.TestCase):
    def test_rss_campos_principais(self):
        itens = parser.interpretar(amostras.RSS, "RSS")
        self.assertEqual(len(itens), 3)
        primeiro = itens[0]
        self.assertEqual(primeiro.titulo, "Senado aprova reforma tributaria em segundo turno")
        self.assertEqual(primeiro.id_externo, "exemplo-10")
        self.assertEqual(primeiro.autor, "Maria Souza")
        self.assertEqual(primeiro.categorias, ["Politica"])
        self.assertEqual(primeiro.imagem, "https://img.test/g.jpg")  # a maior media:content
        self.assertIn("Paragrafo completo", primeiro.conteudo)
        self.assertEqual(primeiro.publicado_em, datetime(2026, 9, 29, 13, 0, tzinfo=timezone.utc))

    def test_rss_imagem_por_enclosure_e_ausente(self):
        itens = parser.interpretar(amostras.RSS, "RSS")
        self.assertEqual(itens[1].imagem, "https://img.test/futebol.png")
        self.assertEqual(itens[2].imagem, "")
        self.assertIsNone(itens[2].publicado_em)

    def test_atom(self):
        (item,) = parser.interpretar(amostras.ATOM, "RSS")
        self.assertEqual(item.url, "https://blog.test/vacina")
        self.assertEqual(item.imagem, "https://img.test/vacina.jpg")
        self.assertEqual(item.autor, "Joao Lima")
        self.assertEqual(item.categorias, ["Saude"])
        self.assertEqual(item.atualizado_em, datetime(2026, 9, 28, 12, 15, tzinfo=timezone.utc))
        self.assertIn("Ministerio", texto_limpo(item.resumo))

    def test_rss_1_rdf(self):
        (item,) = parser.interpretar(amostras.RDF, "RSS")
        self.assertEqual(item.url, "https://rdf.test/a")
        self.assertEqual(item.categorias, ["Ciencia"])

    def test_entidades_html_sao_corrigidas(self):
        (item,) = parser.interpretar(amostras.RSS_ENTIDADES_HTML, "RSS")
        self.assertEqual(item.titulo, "Café & cia\xa0abre loja")

    def test_bloqueia_entidades_declaradas(self):
        with self.assertRaises(parser.ErroFeed):
            parser.interpretar(amostras.RSS_ENTIDADE_PERIGOSA, "RSS")

    def test_conteudo_invalido(self):
        with self.assertRaises(parser.ErroFeed):
            parser.interpretar(b"<html><body>nao e feed</body></html>", "RSS")
        with self.assertRaises(parser.ErroFeed):
            parser.interpretar(b"", "RSS")
        with self.assertRaises(parser.ErroFeed):
            parser.interpretar(b"{nao json", "JSON_FEED")

    def test_json_feed(self):
        (item,) = parser.interpretar(amostras.JSON_FEED, "JSON_FEED")
        self.assertEqual(item.id_externo, "j-1")
        self.assertEqual(item.autor, "Ana")
        self.assertEqual(item.categorias, ["Tecnologia"])

    def test_api_json_com_mapeamento(self):
        (item,) = parser.interpretar(amostras.API_JSON, "API_JSON", amostras.MAPEAMENTO_API)
        self.assertEqual(item.url, "https://api.test/economia/1")
        self.assertEqual(item.imagem, "https://img.test/ipca.jpg")
        self.assertEqual(item.autor, "Carla")
        self.assertEqual(item.categorias, ["Economia"])
        self.assertEqual(item.publicado_em, datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc))

    def test_api_json_caminho_errado(self):
        with self.assertRaises(parser.ErroFeed):
            parser.interpretar(amostras.API_JSON, "API_JSON", {"itens": "nao.existe"})

    def test_datas(self):
        self.assertEqual(parser.interpretar_data("2026-09-29T10:00:00-0300"),
                         datetime(2026, 9, 29, 13, 0, tzinfo=timezone.utc))
        self.assertIsNone(parser.interpretar_data("ontem a tarde"))
        self.assertIsNotNone(parser.interpretar_data(1790000000))


class TextoTests(unittest.TestCase):
    def test_normalizar_url_remove_rastreio_e_fragmento(self):
        self.assertEqual(
            normalizar_url("HTTPS://Exemplo.TEST:443/politica/reforma/?utm_source=rss&id=10&fbclid=x#topo"),
            "https://exemplo.test/politica/reforma?id=10",
        )
        self.assertEqual(normalizar_url("https://a.test"), "https://a.test/")

    def test_url_segura(self):
        self.assertEqual(url_segura("javascript:alert(1)"), "")
        self.assertEqual(url_segura("data:image/png;base64,xx"), "")
        self.assertEqual(url_segura("//sem-esquema.test/x"), "")
        self.assertEqual(url_segura(" https://ok.test/a "), "https://ok.test/a")

    def test_sanitizar_remove_perigos(self):
        html = sanitizar_html(
            '<p onclick="x()">Oi <a href="javascript:alert(1)">ruim</a> '
            '<a href="https://ok.test">bom</a></p><script>alert(1)</script>'
            '<img src=x onerror=alert(1)><iframe src="https://x.test"></iframe>'
        )
        self.assertNotIn("script", html)
        self.assertNotIn("onclick", html)
        self.assertNotIn("javascript", html)
        self.assertNotIn("<img", html)
        self.assertNotIn("iframe", html)
        self.assertIn('<a href="https://ok.test" target="_blank" rel="noopener noreferrer nofollow">bom</a>', html)
        self.assertIn("ruim", html)

    def test_sanitizar_texto_puro_vira_paragrafo(self):
        self.assertEqual(sanitizar_html("Linha simples & <segura>"), "<p>Linha simples &amp;</p>")
        self.assertEqual(sanitizar_html("A<br><br>B"), "<p>A</p><p>B</p>")
        self.assertEqual(sanitizar_html(""), "")

    def test_sanitizar_fecha_tags_abertas(self):
        self.assertEqual(sanitizar_html("<p><strong>forte"), "<p><strong>forte</strong></p>")
        self.assertEqual(sanitizar_html("<div>um</div><div>dois</div>"), "<p>um</p><p>dois</p>")

    def test_texto_limpo_e_resumo(self):
        self.assertEqual(texto_limpo("<p>Oi&nbsp;<b>mundo</b></p><style>x{}</style>"), "Oi mundo")
        texto = "palavra " * 100
        curto = resumir(texto, 50)
        self.assertLessEqual(len(curto), 50)
        self.assertTrue(curto.endswith("…"))

    def test_hash_e_normalizacao(self):
        self.assertEqual(normalizar_texto("  Ação, já!  "), "acao ja")
        self.assertEqual(gerar_hash(1, "a b"), gerar_hash("1", "a b"))
        self.assertNotEqual(gerar_hash(1, "a"), gerar_hash(2, "a"))


class CategorizacaoTests(unittest.TestCase):
    def setUp(self):
        self.categorizador = Categorizador.montar(
            categoria_padrao=1,
            mapeamentos=[(True, "Futebol", 6), (False, "Politica & Governo", 3)],
            categorias=[(3, "Política", "politica"), (4, "Economia", "economia"),
                        (6, "Esportes", "esportes"), (7, "Saúde", "saude")],
            regras=[(4, "inflação, juros, IPCA", 1), (7, "vacina, SUS", 1),
                    (6, "futebol, gol", 1)],
        )

    def test_mapeamento_da_fonte_vence(self):
        self.assertEqual(self.categorizador.categorizar("x", "", ["futebol"]), (6, "mapeamento_fonte"))

    def test_mapeamento_global(self):
        self.assertEqual(self.categorizador.categorizar("x", "", ["POLÍTICA & governo"]),
                         (3, "mapeamento_global"))

    def test_nome_igual_ao_da_categoria(self):
        self.assertEqual(self.categorizador.categorizar("x", "", ["Saude"]), (7, "nome_categoria"))

    def test_palavras_chave_no_titulo(self):
        self.assertEqual(self.categorizador.categorizar("Inflação desacelera em setembro"),
                         (4, "palavras_chave"))

    def test_palavra_so_no_resumo_nao_basta(self):
        self.assertEqual(self.categorizador.categorizar("Notícia", "fala de juros"), (1, "padrao"))

    def test_palavra_inteira(self):
        # "gol" nao pode casar com "golpe"
        self.assertEqual(self.categorizador.categorizar("Golpe do falso boleto"), (1, "padrao"))

    def test_sem_pistas_usa_padrao(self):
        self.assertEqual(self.categorizador.categorizar("Frente fria chega"), (1, "padrao"))


class ImagemTests(unittest.TestCase):
    def test_tag_imagem_destaque_vence_o_logo_do_texto(self):
        itens = parser.interpretar(amostras.RSS_LOGO_NO_TEXTO, "RSS")
        self.assertEqual(
            itens[0].imagem, "https://imagens.test/1170x700/smart/https://abr.test/files/dolar.jpg?itok=aJ")

    def test_pula_logo_e_le_imagem_de_carregamento_preguicoso(self):
        itens = parser.interpretar(amostras.RSS_LOGO_NO_TEXTO, "RSS")
        self.assertEqual(
            itens[1].imagem, "https://imagens.test/754x0/smart/https://abr.test/files/foto.jpg?itok=z")

    def test_so_logo_nao_vira_foto(self):
        itens = parser.interpretar(amostras.RSS_LOGO_NO_TEXTO, "RSS")
        self.assertEqual(itens[2].imagem, "")

    def test_imagem_util(self):
        for ruim in (
            "https://x.test/logo.png", "https://x.test/a/logo-agencia.svg",
            "https://x.test/ebc.png?id=1&o=rss", "https://x.test/spacer.gif",
            "https://x.test/icone.svg", "data:image/png;base64,AAAA", "",
        ):
            self.assertFalse(imagem_util(ruim), ruim)
        self.assertFalse(imagem_util("https://x.test/foto.jpg", alt="Logo do site"))
        self.assertFalse(imagem_util("https://x.test/foto.jpg", estilo="width:1px; height:1px"))
        # palavras que apenas contem "logo" sao fotos normais
        for boa in ("https://x.test/catalogo-2026.jpg", "https://x.test/dialogo.png",
                    "https://x.test/foto.jpg?itok=abc"):
            self.assertTrue(imagem_util(boa), boa)


if __name__ == "__main__":
    unittest.main()
