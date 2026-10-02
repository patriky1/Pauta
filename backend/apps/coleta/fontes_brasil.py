"""Catalogo de fontes brasileiras confiaveis (RSS), usado por `manage.py coleta_fontes`.

Criterios: veiculos jornalisticos ou agencias publicas reconhecidas, com feed RSS oficial
e publico (sem scraping, sem paywall). Enderecos conferidos em 10/2026.

Direitos: por padrao so o RESUMO e importado, com credito e link para a materia original.
As agencias publicas (Agencia Brasil, Agencia Camara) autorizam a reproducao com credito;
se quiser o texto integral delas, marque "importar conteudo completo" no /django-admin/
depois de conferir os termos atuais. Para os veiculos comerciais (g1, Folha, BBC),
mantenha apenas o resumo.

Campos: nome, url_feed, url_site, slug da categoria padrao do site.
"""

FONTES_BRASILEIRAS = [
    # agencias publicas
    ("Agência Brasil — Últimas notícias",
     "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml",
     "https://agenciabrasil.ebc.com.br", "brasil"),
    ("Agência Brasil — Economia",
     "https://agenciabrasil.ebc.com.br/rss/economia/feed.xml",
     "https://agenciabrasil.ebc.com.br", "economia"),
    ("Agência Câmara de Notícias",
     "https://www.camara.leg.br/noticias/rss/ultimas-noticias",
     "https://www.camara.leg.br/noticias", "politica"),
    # veiculos nacionais
    ("g1 — Últimas notícias", "https://g1.globo.com/rss/g1/",
     "https://g1.globo.com", "brasil"),
    ("g1 — Política", "https://g1.globo.com/rss/g1/politica",
     "https://g1.globo.com/politica/", "politica"),
    ("g1 — Economia", "https://g1.globo.com/rss/g1/economia",
     "https://g1.globo.com/economia/", "economia"),
    ("g1 — Mundo", "https://g1.globo.com/rss/g1/mundo",
     "https://g1.globo.com/mundo/", "mundo"),
    ("g1 — Ciência e Saúde", "https://g1.globo.com/rss/g1/ciencia-e-saude",
     "https://g1.globo.com/ciencia-e-saude/", "ciencia"),
    ("g1 — Educação", "https://g1.globo.com/rss/g1/educacao",
     "https://g1.globo.com/educacao/", "educacao"),
    ("Folha de S.Paulo — Em cima da hora",
     "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml",
     "https://www.folha.uol.com.br", "brasil"),
    ("BBC News Brasil", "https://feeds.bbci.co.uk/portuguese/rss.xml",
     "https://www.bbc.com/portuguese", "mundo"),
]
