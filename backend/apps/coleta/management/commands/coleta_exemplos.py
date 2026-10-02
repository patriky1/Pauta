"""Cria regras de palavras-chave para as categorias existentes e fontes de exemplo.

    python manage.py coleta_exemplos
    python manage.py coleta_exemplos --ativar      # ja deixa as fontes ativas

E idempotente: pode rodar varias vezes sem duplicar nada. As fontes de exemplo sao da
Agencia Brasil (EBC), cujo conteudo e publicado sob licenca Creative Commons BY
(republicacao permitida com credito) — confira sempre os termos atuais da fonte.
"""
from django.core.management.base import BaseCommand, CommandError

from apps.categories.models import Categoria
from apps.coleta.models import FonteNoticia, MapeamentoCategoria, RegraCategorizacao
from apps.coleta.texto import normalizar_texto

PALAVRAS = {
    "politica": "política, congresso, senado, câmara dos deputados, deputado, deputada, senador, "
                "senadora, eleição, eleições, eleitoral, STF, Supremo Tribunal Federal, Planalto, "
                "partido, governador, prefeito, ministro, ministra, reforma política",
    "economia": "economia, inflação, IPCA, Selic, juros, PIB, dólar, câmbio, Ibovespa, "
                "Banco Central, mercado financeiro, reforma tributária, imposto, arrecadação, "
                "desemprego, emprego formal, salário mínimo, Receita Federal",
    "tecnologia": "tecnologia, inteligência artificial, software, aplicativo, internet, startup, "
                  "smartphone, celular, cibersegurança, ataque hacker, dados pessoais, LGPD, "
                  "big tech, semicondutor",
    "esportes": "futebol, campeonato, brasileirão, Copa do Mundo, seleção brasileira, "
                "Libertadores, Olimpíadas, Paralimpíadas, vôlei, basquete, Fórmula 1, atleta, "
                "gol, partida",
    "saude": "saúde, SUS, hospital, vacina, vacinação, doença, Anvisa, epidemia, dengue, "
             "covid, Ministério da Saúde, câncer, atendimento médico",
    "educacao": "educação, escola, Enem, universidade, ensino, professor, professora, estudante, "
                "MEC, vestibular, Sisu, Prouni, Fies, alfabetização",
    "seguranca": "polícia, policial, crime, prisão, preso, homicídio, assalto, segurança pública, "
                 "operação policial, Polícia Federal, tráfico, investigação",
    "cultura": "cultura, cinema, filme, música, show, festival, livro, teatro, exposição, museu, "
               "patrimônio cultural, artista",
    "entretenimento": "celebridade, novela, streaming, reality show, famosos, influenciador",
    "ciencia": "ciência, cientistas, NASA, astronomia, telescópio, pesquisa científica, "
               "meio ambiente, clima, aquecimento global, desmatamento, biodiversidade",
    "mundo": "internacional, Estados Unidos, EUA, China, Rússia, Ucrânia, Europa, ONU, Israel, "
             "Gaza, Argentina, União Europeia",
    "cidades": "trânsito, prefeitura, obras, transporte público, mobilidade urbana, metrô, "
               "saneamento, enchente, bairro",
}

# URLs de RSS publicadas pela Agencia Brasil
FONTES = [
    ("Agência Brasil — Últimas notícias",
     "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml", "brasil"),
    ("Agência Brasil — Economia",
     "https://agenciabrasil.ebc.com.br/rss/economia/feed.xml", "economia"),
]


class Command(BaseCommand):
    help = "Cria regras de categorizacao e fontes de exemplo (Agencia Brasil)."

    def add_arguments(self, parser):
        parser.add_argument("--ativar", action="store_true", help="Cria as fontes ja ativas.")

    def handle(self, *args, **opcoes):
        categorias = {normalizar_texto(c.nome): c for c in Categoria.objects.all()}
        if not categorias:
            raise CommandError("Cadastre as categorias primeiro (ou rode seed_data).")

        regras = 0
        for chave, palavras in PALAVRAS.items():
            categoria = categorias.get(chave)
            if not categoria:
                continue
            _, criada = RegraCategorizacao.objects.get_or_create(
                categoria=categoria, defaults={"palavras_chave": palavras})
            regras += int(criada)

        padrao_geral = categorias.get("brasil") or Categoria.objects.filter(ativa=True).first()
        fontes = 0
        for nome, url, categoria in FONTES:
            fonte, criada = FonteNoticia.objects.get_or_create(
                url_feed=url,
                defaults={
                    "nome": nome,
                    "url_site": "https://agenciabrasil.ebc.com.br",
                    "categoria_padrao": categorias.get(categoria) or padrao_geral,
                    "ativa": opcoes["ativar"],
                    "importar_conteudo_completo": False,
                },
            )
            fontes += int(criada)

        for termo, chave in (("Política", "politica"), ("Economia", "economia"),
                             ("Saúde", "saude"), ("Educação", "educacao"),
                             ("Esportes", "esportes"), ("Internacional", "mundo"),
                             ("Geral", "brasil")):
            if categorias.get(chave):
                MapeamentoCategoria.objects.get_or_create(
                    fonte=None, termo_origem=termo,
                    defaults={"categoria": categorias[chave]})

        situacao = "ativas" if opcoes["ativar"] else "INATIVAS (ative no /django-admin/)"
        self.stdout.write(self.style.SUCCESS(
            f"{regras} regra(s) de palavras-chave e {fontes} fonte(s) {situacao} criadas."
        ))
