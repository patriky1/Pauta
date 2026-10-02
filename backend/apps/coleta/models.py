from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import ModeloBase
from apps.core.utils import slug_unico


class FonteNoticia(ModeloBase):
    """Fonte externa (feed RSS/Atom, JSON Feed ou API) cadastrada pelo painel.

    Diferente de `news.Fonte`, que guarda as fontes citadas dentro de uma materia.
    """

    class Tipo(models.TextChoices):
        RSS = "RSS", "RSS / Atom"
        JSON_FEED = "JSON_FEED", "JSON Feed"
        API_JSON = "API_JSON", "API JSON (com mapeamento)"

    nome = models.CharField("nome", max_length=120, unique=True)
    slug = models.SlugField("slug", max_length=140, unique=True, blank=True)
    url_site = models.URLField("site da fonte", max_length=500, blank=True)
    url_feed = models.URLField(
        "URL do feed/API", max_length=1000, unique=True,
        help_text="Endereco do RSS/Atom, JSON Feed ou da API oficial.",
    )
    tipo = models.CharField("tipo", max_length=10, choices=Tipo.choices, default=Tipo.RSS)
    ativa = models.BooleanField("ativa", default=True, db_index=True)
    categoria_padrao = models.ForeignKey(
        "categories.Categoria", on_delete=models.PROTECT, related_name="fontes_externas",
        verbose_name="categoria padrao",
        help_text="Usada quando nenhum mapeamento ou palavra-chave identifica a categoria.",
    )

    publicar_automaticamente = models.BooleanField(
        "publicar automaticamente", default=True,
        help_text="Desmarque para que as notícias entrem como 'Em revisão' no painel.",
    )
    importar_conteudo_completo = models.BooleanField(
        "importar conteudo completo", default=False,
        help_text="Marque apenas se a licença da fonte permitir republicar o texto integral "
                  "(ex.: Creative Commons). Caso contrário, só o resumo é importado.",
    )
    buscar_imagem_na_pagina = models.BooleanField(
        "buscar imagem na pagina original", default=False,
        help_text="Quando o feed não traz imagem, lê a og:image da página (respeita robots.txt).",
    )
    limite_por_coleta = models.PositiveSmallIntegerField("itens por coleta", default=30)

    mapeamento_json = models.JSONField(
        "mapeamento da API", default=dict, blank=True,
        help_text='Somente para "API JSON". Ex.: {"itens": "articles", "titulo": "title", '
                  '"url": "url", "resumo": "description", "imagem": "urlToImage", '
                  '"data": "publishedAt", "autor": "author", "id": "url"}',
    )
    chave_api_variavel = models.CharField(
        "variavel de ambiente da chave", max_length=80, blank=True,
        help_text="NOME da variável do .env com a chave (ex.: NEWSAPI_KEY). "
                  "A chave em si nunca fica no banco.",
    )
    chave_api_parametro = models.CharField(
        "como enviar a chave", max_length=80, blank=True,
        help_text="Nome do parâmetro na URL (ex.: apiKey) ou 'header:Nome-Do-Cabecalho'.",
    )

    # estado da sincronizacao (preenchido pela coleta)
    ultima_sincronizacao = models.DateTimeField("ultima sincronizacao", blank=True, null=True)
    ultimo_sucesso = models.DateTimeField("ultimo sucesso", blank=True, null=True)
    ultimo_erro = models.TextField("ultimo erro", blank=True)
    erros_consecutivos = models.PositiveIntegerField("erros consecutivos", default=0)
    total_importadas = models.PositiveIntegerField("total importadas", default=0)
    etag = models.CharField("ETag", max_length=255, blank=True)
    ultima_modificacao = models.CharField("Last-Modified", max_length=100, blank=True)

    class Meta:
        verbose_name = "fonte de noticias"
        verbose_name_plural = "fontes de noticias"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slug_unico(FonteNoticia, self.nome, self)
        super().save(*args, **kwargs)


class MapeamentoCategoria(models.Model):
    """Traduz a categoria que vem no feed para uma categoria do site."""

    fonte = models.ForeignKey(
        FonteNoticia, on_delete=models.CASCADE, related_name="mapeamentos",
        blank=True, null=True, verbose_name="fonte",
        help_text="Deixe vazio para valer para todas as fontes.",
    )
    termo_origem = models.CharField(
        "categoria na fonte", max_length=120,
        help_text="Como aparece no feed. Maiúsculas e acentos são ignorados na comparação.",
    )
    categoria = models.ForeignKey(
        "categories.Categoria", on_delete=models.CASCADE, related_name="mapeamentos_coleta",
        verbose_name="categoria no site",
    )

    class Meta:
        verbose_name = "mapeamento de categoria"
        verbose_name_plural = "mapeamentos de categoria"
        ordering = ["fonte__nome", "termo_origem"]
        constraints = [
            models.UniqueConstraint(
                fields=["fonte", "termo_origem"], name="coleta_mapeamento_unico_por_fonte",
            ),
            models.UniqueConstraint(
                fields=["termo_origem"], condition=Q(fonte__isnull=True),
                name="coleta_mapeamento_global_unico",
            ),
        ]

    def __str__(self):
        escopo = self.fonte.nome if self.fonte_id else "todas as fontes"
        return f"{self.termo_origem} -> {self.categoria} ({escopo})"


class RegraCategorizacao(models.Model):
    """Palavras-chave que indicam uma categoria (categorizacao automatica)."""

    categoria = models.ForeignKey(
        "categories.Categoria", on_delete=models.CASCADE, related_name="regras_coleta",
        verbose_name="categoria",
    )
    palavras_chave = models.TextField(
        "palavras-chave",
        help_text="Separe por vírgula ou uma por linha. Ex.: inflação, juros, IPCA, Banco Central",
    )
    peso = models.PositiveSmallIntegerField("peso", default=1)
    ativa = models.BooleanField("ativa", default=True)

    class Meta:
        verbose_name = "regra de categorizacao"
        verbose_name_plural = "regras de categorizacao"
        ordering = ["categoria__nome"]

    def __str__(self):
        return f"{self.categoria}: {self.palavras_chave[:60]}"


class ExecucaoColeta(models.Model):
    """Log de cada sincronizacao de cada fonte."""

    class Status(models.TextChoices):
        EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
        SUCESSO = "SUCESSO", "Sucesso"
        PARCIAL = "PARCIAL", "Sucesso com erros"
        ERRO = "ERRO", "Erro"

    fonte = models.ForeignKey(
        FonteNoticia, on_delete=models.CASCADE, related_name="execucoes", verbose_name="fonte",
    )
    status = models.CharField("status", max_length=12, choices=Status.choices,
                              default=Status.EM_ANDAMENTO, db_index=True)
    iniciada_em = models.DateTimeField("iniciada em", default=timezone.now, db_index=True)
    finalizada_em = models.DateTimeField("finalizada em", blank=True, null=True)
    itens_lidos = models.PositiveIntegerField("itens lidos", default=0)
    novas = models.PositiveIntegerField("novas", default=0)
    atualizadas = models.PositiveIntegerField("atualizadas", default=0)
    ignoradas = models.PositiveIntegerField("ignoradas", default=0)
    mensagem = models.TextField("mensagem", blank=True)

    class Meta:
        verbose_name = "execucao da coleta"
        verbose_name_plural = "execucoes da coleta"
        ordering = ["-iniciada_em"]
        indexes = [models.Index(fields=["fonte", "-iniciada_em"], name="coleta_exec_fonte_data_idx")]

    def __str__(self):
        return f"{self.fonte} - {self.iniciada_em:%d/%m %H:%M} - {self.get_status_display()}"

    @property
    def duracao_segundos(self):
        if not self.finalizada_em:
            return None
        return round((self.finalizada_em - self.iniciada_em).total_seconds(), 2)
