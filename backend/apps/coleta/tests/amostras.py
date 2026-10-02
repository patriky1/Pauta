"""Feeds de exemplo usados nos testes (conteudo ficticio)."""

RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>Agencia Exemplo</title>
    <link>https://exemplo.test</link>
    <item>
      <title>Senado aprova reforma tributaria em segundo turno</title>
      <link>https://exemplo.test/politica/reforma?utm_source=rss&amp;id=10#topo</link>
      <guid isPermaLink="false">exemplo-10</guid>
      <description><![CDATA[<p>Texto aprovado segue para a <b>Camara</b>.</p><script>alert(1)</script>]]></description>
      <content:encoded><![CDATA[<p>Paragrafo completo.</p><p onclick="x()">Segundo <a href="javascript:alert(1)">link ruim</a> e <a href="https://fonte.test/doc">documento</a>.</p><img src="https://img.test/corpo.jpg">]]></content:encoded>
      <dc:creator>Maria Souza</dc:creator>
      <category>Politica</category>
      <media:content url="https://img.test/p.jpg" medium="image" width="300"/>
      <media:content url="https://img.test/g.jpg" medium="image" width="1200"/>
      <pubDate>Tue, 29 Sep 2026 10:00:00 -0300</pubDate>
    </item>
    <item>
      <title>Selecao brasileira vence amistoso com gol no fim</title>
      <link>https://exemplo.test/esportes/amistoso</link>
      <description>O time venceu por 1 a 0 no campeonato amistoso.</description>
      <enclosure url="https://img.test/futebol.png" type="image/png" length="1"/>
      <category>Futebol</category>
      <pubDate>Tue, 29 Sep 2026 11:30:00 GMT</pubDate>
    </item>
    <item>
      <title>Nota sem imagem sobre o clima</title>
      <link>https://exemplo.test/geral/clima</link>
      <description>Frente fria chega ao Sul.</description>
    </item>
  </channel>
</rss>"""

RSS_ATUALIZADO = RSS.replace(
    b"Senado aprova reforma tributaria em segundo turno",
    b"Senado aprova reforma tributaria em segundo turno; texto vai a sancao",
)

RSS_ENTIDADES_HTML = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>X</title>
<item><title>Caf&eacute; &amp; cia&nbsp;abre loja</title><link>https://exemplo.test/cafe</link>
<description>Pre&ccedil;o &mdash; baixo</description></item>
</channel></rss>"""

RSS_ENTIDADE_PERIGOSA = b"""<?xml version="1.0"?>
<!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;">]>
<rss><channel><item><title>&lol2;</title></item></channel></rss>"""

ATOM = b"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Blog Exemplo</title>
  <entry>
    <title>Nova vacina contra dengue chega ao SUS</title>
    <link rel="alternate" type="text/html" href="https://blog.test/vacina"/>
    <link rel="enclosure" type="image/jpeg" href="https://img.test/vacina.jpg"/>
    <id>tag:blog.test,2026:vacina</id>
    <published>2026-09-28T08:00:00Z</published>
    <updated>2026-09-28T09:15:00-03:00</updated>
    <author><name>Joao Lima</name></author>
    <category term="saude" label="Saude"/>
    <summary type="html">&lt;p&gt;Ministerio amplia a vacinacao.&lt;/p&gt;</summary>
  </entry>
</feed>"""

RDF = b"""<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/"
  xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel rdf:about="https://rdf.test"><title>RDF</title></channel>
  <item rdf:about="https://rdf.test/a">
    <title>Item RDF</title><link>https://rdf.test/a</link>
    <dc:date>2026-09-27T12:00:00+00:00</dc:date><dc:subject>Ciencia</dc:subject>
  </item>
</rdf:RDF>"""

JSON_FEED = {
    "version": "https://jsonfeed.org/version/1.1",
    "title": "JSON Exemplo",
    "items": [
        {
            "id": "j-1",
            "url": "https://json.test/1",
            "title": "Startup lanca aplicativo de inteligencia artificial",
            "summary": "Ferramenta usa IA.",
            "image": "https://img.test/app.jpg",
            "date_published": "2026-09-29T12:00:00Z",
            "authors": [{"name": "Ana"}],
            "tags": ["Tecnologia"],
        }
    ],
}

API_JSON = {
    "status": "ok",
    "dados": {
        "artigos": [
            {
                "titulo": "Inflacao desacelera e juros podem cair",
                "link": "https://api.test/economia/1",
                "descricao": "IPCA fica abaixo do esperado.",
                "capa": {"url": "https://img.test/ipca.jpg"},
                "publicado": "2026-09-29T09:00:00-03:00",
                "editoria": "Economia",
                "autor": {"nome": "Carla"},
            }
        ]
    },
}

MAPEAMENTO_API = {
    "itens": "dados.artigos",
    "titulo": "titulo",
    "url": "link",
    "id": "link",
    "resumo": "descricao",
    "imagem": "capa.url",
    "data": "publicado",
    "autor": "autor",
    "categorias": "editoria",
}


# Estrutura real do feed da Agencia Brasil: a foto vem em <imagem-destaque> e o texto
# comeca com o <img> do logo e termina com pixels de rastreamento.
RSS_LOGO_NO_TEXTO = b"""<?xml version="1.0" encoding="utf-8" ?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/"><channel><title>Feed</title>
<item><title>Deficit nas contas externas soma US$ 5,1 bilhoes</title>
<link>https://abr.test/economia/deficit</link>
<imagem-destaque>https://imagens.test/1170x700/smart/https://abr.test/files/dolar.jpg?itok=aJ</imagem-destaque>
<description>&lt;p style=&quot;text-align:center;&quot;&gt;&lt;a href=&quot;https://abr.test/x&quot;&gt;&lt;img src=&quot;https://cdn.test/assets/logo-agenciabrasil.svg&quot; alt=&quot;Logo Agencia&quot;&gt;&lt;/a&gt;&lt;/p&gt;&lt;strong&gt;O deficit somou US$ 5,1 bilhoes.&lt;/strong&gt;&lt;img src=&quot;https://abr.test/ebc.png?id=1&amp;amp;o=rss&quot; style=&quot;width:1px; height:1px;&quot; /&gt;</description>
<pubDate>Mon, 28 Sep 2026 11:05:00 -0300</pubDate><guid isPermaLink="false">1703522 at abr.test</guid></item>
<item><title>Foto so no texto, com carregamento preguicoso</title>
<link>https://abr.test/economia/lazy</link>
<description>&lt;img src=&quot;https://cdn.test/assets/logo-agenciabrasil.svg&quot; alt=&quot;Logo&quot;&gt;&lt;img src=&quot;/files/loading_v2.gif&quot; data-echo=&quot;https://imagens.test/754x0/smart/https://abr.test/files/foto.jpg?itok=z&quot;&gt;</description>
<guid>lazy-1</guid></item>
<item><title>Somente o logo, sem foto nenhuma</title>
<link>https://abr.test/economia/sem-foto</link>
<description>&lt;img src=&quot;https://cdn.test/assets/logo-agenciabrasil.svg&quot; alt=&quot;Logo&quot;&gt;&lt;p&gt;texto&lt;/p&gt;</description>
<guid>sem-foto-1</guid></item>
</channel></rss>"""
