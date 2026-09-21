"""Popula o banco com dados ficticios de demonstracao.

Uso: python manage.py seed_data [--reset]
Todo o conteudo gerado aqui e ficticio e serve apenas para avaliar a interface.
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.analytics.models import Evento
from apps.categories.models import Categoria, Tag
from apps.comments.models import Comentario, CurtidaComentario
from apps.interactions.models import CategoriaSeguida, Favorito
from apps.news.models import (
    Anuncio,
    AtualizacaoAoVivo,
    CoberturaAoVivo,
    Fonte,
    Noticia,
    StatusNoticia,
    Video,
)
from apps.notifications.models import Notificacao
from apps.users.models import TipoUsuario, User

CATEGORIAS = [
    ("Brasil", "#1B48C4"), ("Mundo", "#0E7490"), ("Politica", "#7C3AED"),
    ("Economia", "#047857"), ("Tecnologia", "#2563EB"), ("Esportes", "#D97706"),
    ("Saude", "#DB2777"), ("Educacao", "#4338CA"), ("Seguranca", "#B91C1C"),
    ("Cultura", "#9333EA"), ("Entretenimento", "#DB2777"), ("Ciencia", "#0891B2"),
    ("Cidades", "#57534E"),
]

TAGS = [
    "eleicoes", "inteligencia artificial", "inflacao", "copa", "clima", "startups",
    "educacao publica", "saude mental", "mobilidade", "energia", "seguranca digital",
    "mercado de trabalho", "espaco", "cinema", "musica", "agro",
]

MANCHETES = [
    "Nova politica de dados entra em vigor e muda regras para plataformas",
    "Pesquisa aponta avanco de energia solar em residencias brasileiras",
    "Selecao confirma amistoso e tecnico anuncia lista de convocados",
    "Startups de saude digital captam recorde de investimento no trimestre",
    "Ministerio anuncia programa de reforco escolar para a rede publica",
    "Estudo relaciona sono irregular a queda de produtividade no trabalho",
    "Cidade inaugura corredor de onibus e promete reduzir tempo de viagem",
    "Inflacao desacelera pelo terceiro mes seguido, aponta indice oficial",
    "Telescopio registra formacao de estrela a milhares de anos-luz",
    "Festival de cinema anuncia selecao com dez producoes nacionais",
    "Setor de tecnologia abre vagas e aquece o mercado de trabalho",
    "Nova linha de credito para pequenos negocios comeca nesta semana",
    "Pesquisadores desenvolvem material que reduz consumo de agua na industria",
    "Campeonato define tabela e jogos terao novo horario aos domingos",
    "Plano de seguranca preve mais cameras em areas de grande circulacao",
    "Exportacoes do agronegocio crescem e puxam saldo comercial do mes",
    "Museu digitaliza acervo e abre consulta gratuita pela internet",
    "Hospitais ampliam atendimento e reduzem fila de cirurgias eletivas",
    "Acordo internacional estabelece metas de reducao de emissoes",
    "Aplicativo de transporte publico passa a mostrar lotacao em tempo real",
    "Universidade abre inscricoes para cursos gratuitos de programacao",
    "Bolsas fecham em alta apos divulgacao de dados de emprego",
    "Time local conquista vaga na final apos virada no segundo tempo",
    "Campanha de vacinacao amplia publico e funciona em fim de semana",
]

PARAGRAFOS = [
    "A medida foi divulgada nesta semana e passa a valer para todo o territorio nacional. "
    "Especialistas ouvidos pela reportagem avaliam que o impacto deve aparecer nos proximos meses.",
    "Os dados mostram uma mudanca consistente em relacao ao mesmo periodo do ano anterior. "
    "O levantamento considerou uma amostra ampla e foi revisado por pesquisadores independentes.",
    "Entidades do setor afirmam que o cenario exige planejamento e investimento continuo. "
    "Ha divergencia, porem, sobre o ritmo das mudancas e sobre quem arca com os custos.",
    "Em nota, os responsaveis informaram que as proximas etapas serao detalhadas em audiencia publica. "
    "A reportagem procurou todas as partes citadas e publicara eventuais respostas.",
    "Para quem acompanha o assunto de perto, o ponto central esta na execucao. "
    "O cronograma prevê revisao trimestral e divulgacao aberta dos resultados.",
]

COMENTARIOS = [
    "Materia bem apurada, obrigado pelo contexto.",
    "Faltou detalhar o impacto para quem mora no interior.",
    "Acompanho esse assunto ha meses e finalmente vi uma explicacao clara.",
    "Interessante, mas gostaria de ver as fontes completas.",
    "Boa cobertura. Continuem acompanhando o desdobramento.",
    "Discordo da conclusao, embora os dados sejam uteis.",
]


class Command(BaseCommand):
    help = "Cria dados ficticios de demonstracao (usuarios, categorias, noticias, comentarios)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Apaga o conteudo de demonstracao antes de criar.")
        parser.add_argument("--noticias", type=int, default=48)

    @transaction.atomic
    def handle(self, *args, **opcoes):
        random.seed(42)
        if opcoes["reset"]:
            self.stdout.write("Limpando conteudo anterior...")
            Evento.objects.all().delete()
            Notificacao.objects.all().delete()
            CurtidaComentario.objects.all().delete()
            Comentario.objects.all().delete()
            Favorito.objects.all().delete()
            AtualizacaoAoVivo.objects.all().delete()
            CoberturaAoVivo.objects.all().delete()
            Fonte.objects.all().delete()
            Noticia.objects.all().delete()
            Video.objects.all().delete()
            Anuncio.objects.all().delete()

        categorias = self._categorias()
        tags = self._tags()
        equipe, leitores = self._usuarios()
        noticias = self._noticias(opcoes["noticias"], categorias, tags, equipe)
        self._comentarios(noticias, leitores)
        self._interacoes(noticias, leitores, categorias)
        self._ao_vivo(categorias, equipe)
        self._videos(categorias, equipe)
        self._anuncios()
        self._eventos(noticias, leitores)

        self.stdout.write(self.style.SUCCESS(
            f"Pronto. {len(noticias)} noticias, {len(equipe) + len(leitores)} usuarios."
        ))
        self.stdout.write("Acesso de demonstracao: admin@pauta.local / senha: pauta12345")

    # ------------------------------------------------------------------ partes
    def _categorias(self):
        itens = []
        for ordem, (nome, cor) in enumerate(CATEGORIAS):
            categoria, _ = Categoria.objects.get_or_create(
                nome=nome,
                defaults={"cor": cor, "ordem": ordem,
                          "descricao": f"Cobertura de {nome.lower()}."},
            )
            itens.append(categoria)
        return itens

    def _tags(self):
        return [Tag.objects.get_or_create(nome=nome)[0] for nome in TAGS]

    def _usuarios(self):
        base = [
            ("admin", "Ana Ribeiro", TipoUsuario.ADMIN),
            ("editor", "Carlos Menezes", TipoUsuario.EDITOR),
            ("jornalista", "Beatriz Lima", TipoUsuario.JORNALISTA),
            ("marcos", "Marcos Tavares", TipoUsuario.JORNALISTA),
            ("helena", "Helena Duarte", TipoUsuario.AUTOR),
            ("rafael", "Rafael Nogueira", TipoUsuario.AUTOR),
        ]
        equipe = []
        for username, nome, papel in base:
            usuario, criado = User.objects.get_or_create(
                username=username,
                defaults={
                    "nome": nome,
                    "email": f"{username}@pauta.local",
                    "tipo_usuario": papel,
                    "biografia": f"{nome} cobre pautas de interesse publico na redacao do Pauta.",
                    "twitter": f"@{username}",
                    "is_staff": papel in (TipoUsuario.ADMIN, TipoUsuario.EDITOR),
                    "is_superuser": papel == TipoUsuario.ADMIN,
                },
            )
            if criado:
                usuario.set_password("pauta12345")
                usuario.save()
            equipe.append(usuario)

        leitores = []
        for indice in range(1, 13):
            usuario, criado = User.objects.get_or_create(
                username=f"leitor{indice}",
                defaults={"nome": f"Leitor {indice}",
                          "email": f"leitor{indice}@pauta.local"},
            )
            if criado:
                usuario.set_password("pauta12345")
                usuario.save()
            leitores.append(usuario)
        return equipe, leitores

    def _noticias(self, quantidade, categorias, tags, equipe):
        autores = [u for u in equipe if u.tipo_usuario != TipoUsuario.ADMIN] or equipe
        agora = timezone.now()
        criadas = []
        for indice in range(quantidade):
            titulo = MANCHETES[indice % len(MANCHETES)]
            if indice >= len(MANCHETES):
                titulo = f"{titulo} — atualizacao {indice // len(MANCHETES) + 1}"
            categoria = categorias[indice % len(categorias)]
            corpo = "\n\n".join(
                f"<p>{p}</p>" for p in random.sample(PARAGRAFOS, k=4)
            )
            publicacao = agora - timedelta(hours=indice * 5, minutes=random.randint(0, 59))
            noticia = Noticia.objects.create(
                titulo=titulo,
                subtitulo="Entenda o que muda e quais sao os proximos passos",
                conteudo=f"<p><strong>{titulo}.</strong></p>\n\n{corpo}",
                categoria=categoria,
                autor=random.choice(autores),
                status=StatusNoticia.PUBLICADA if indice < quantidade - 4
                else StatusNoticia.RASCUNHO,
                data_publicacao=publicacao,
                destaque=indice < 6,
                breaking_news=indice < 2,
                exclusivo=indice % 7 == 0,
                visualizacoes=random.randint(120, 9800),
                imagem_url=f"https://picsum.photos/seed/pauta{indice}/1200/800",
                imagem_legenda="Imagem ilustrativa de demonstracao",
                imagem_credito="Acervo Pauta",
            )
            noticia.tags.set(random.sample(tags, k=3))
            Fonte.objects.bulk_create([
                Fonte(noticia=noticia, titulo="Nota oficial divulgada pelo orgao"),
                Fonte(noticia=noticia, titulo="Levantamento estatistico do setor"),
            ])
            criadas.append(noticia)
        return criadas

    def _comentarios(self, noticias, leitores):
        for noticia in noticias[:20]:
            for _ in range(random.randint(1, 4)):
                pai = Comentario.objects.create(
                    noticia=noticia,
                    autor=random.choice(leitores),
                    conteudo=random.choice(COMENTARIOS),
                )
                if random.random() > 0.5:
                    Comentario.objects.create(
                        noticia=noticia,
                        autor=random.choice(leitores),
                        resposta_a=pai,
                        conteudo="Boa observacao, tambem fiquei com essa duvida.",
                    )
                for usuario in random.sample(leitores, k=random.randint(0, 3)):
                    CurtidaComentario.objects.get_or_create(comentario=pai, usuario=usuario)

    def _interacoes(self, noticias, leitores, categorias):
        for leitor in leitores:
            for categoria in random.sample(categorias, k=3):
                CategoriaSeguida.objects.get_or_create(usuario=leitor, categoria=categoria)
            for noticia in random.sample(noticias[:25], k=3):
                Favorito.objects.get_or_create(usuario=leitor, noticia=noticia)

    def _ao_vivo(self, categorias, equipe):
        cobertura = CoberturaAoVivo.objects.create(
            titulo="Cobertura ao vivo: votacao do novo marco regulatorio",
            resumo="Acompanhe minuto a minuto as decisoes e os bastidores da sessao.",
            categoria=categorias[2],
            criado_por=equipe[2],
        )
        agora = timezone.now()
        blocos = [
            ("Sessao aberta", "Os trabalhos comecaram com a leitura do relatorio."),
            ("Primeiro destaque rejeitado", "A votacao seguiu para o proximo item da pauta."),
            ("Discussao do texto-base", "Relator apresenta ajustes negociados durante a manha."),
            ("Placar parcial", "A contagem indica maioria favoravel ao texto-base."),
        ]
        for posicao, (titulo, conteudo) in enumerate(blocos):
            AtualizacaoAoVivo.objects.create(
                cobertura=cobertura,
                autor=equipe[2],
                titulo=titulo,
                conteudo=conteudo,
                importante=posicao == 3,
                horario=agora - timedelta(minutes=18 * (len(blocos) - posicao)),
            )

    def _videos(self, categorias, equipe):
        for indice in range(8):
            Video.objects.create(
                titulo=f"Explica: {MANCHETES[indice]}",
                descricao="Resumo em video com os principais pontos da materia.",
                categoria=categorias[indice % len(categorias)],
                autor=equipe[(indice % 4) + 1],
                plataforma=Video.Plataforma.YOUTUBE,
                url="https://www.youtube.com/watch?v=aqz-KE-bpKQ",
                id_externo="aqz-KE-bpKQ",
                thumbnail_url=f"https://picsum.photos/seed/video{indice}/800/450",
                duracao_segundos=random.randint(90, 720),
                visualizacoes=random.randint(200, 5000),
            )

    def _anuncios(self):
        posicoes = [
            (Anuncio.Posicao.TOPO, "Assine o Pauta e leia sem limites"),
            (Anuncio.Posicao.LATERAL, "Newsletter diaria do Pauta"),
            (Anuncio.Posicao.MATERIA, "Podcast Pauta: novo episodio"),
            (Anuncio.Posicao.FEED, "Baixe o app do Pauta"),
        ]
        for posicao, titulo in posicoes:
            Anuncio.objects.get_or_create(
                titulo=titulo,
                posicao=posicao,
                defaults={
                    "anunciante": "Pauta",
                    "url_destino": "https://example.com/assine",
                    "imagem_url": f"https://picsum.photos/seed/{posicao}/960/240",
                },
            )

    def _eventos(self, noticias, leitores):
        agora = timezone.now()
        eventos = []
        for noticia in noticias[:30]:
            for _ in range(random.randint(3, 25)):
                eventos.append(
                    Evento(
                        tipo=Evento.Tipo.VISUALIZACAO,
                        noticia=noticia,
                        categoria=noticia.categoria,
                        usuario=random.choice(leitores + [None]),
                        sessao=f"seed-{random.randint(1, 400)}",
                    )
                )
        Evento.objects.bulk_create(eventos)
        Evento.objects.filter(pk__in=[e.pk for e in eventos[: len(eventos) // 2] if e.pk]).update(
            criado_em=agora - timedelta(days=3)
        )
