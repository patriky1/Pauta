from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import ModeloBase
from apps.core.utils import calcular_tempo_leitura, slug_unico, texto_puro


class StatusNoticia(models.TextChoices):
    RASCUNHO = "RASCUNHO", "Rascunho"
    REVISAO = "REVISAO", "Em revisao"
    AGENDADA = "AGENDADA", "Agendada"
    PUBLICADA = "PUBLICADA", "Publicada"
    ARQUIVADA = "ARQUIVADA", "Arquivada"


class FormatoNoticia(models.TextChoices):
    TEXTO = "TEXTO", "Materia"
    GALERIA = "GALERIA", "Galeria"
    VIDEO = "VIDEO", "Video"
    AUDIO = "AUDIO", "Audio"
    PODCAST = "PODCAST", "Podcast"
    INFOGRAFICO = "INFOGRAFICO", "Infografico"
    AO_VIVO = "AO_VIVO", "Cobertura ao vivo"


class NoticiaQuerySet(models.QuerySet):
    def publicadas(self):
        return self.filter(
            status=StatusNoticia.PUBLICADA, data_publicacao__lte=timezone.now()
        )

    def com_relacionamentos(self):
        return self.select_related("autor", "categoria").prefetch_related("tags")


class NoticiaManager(models.Manager.from_queryset(NoticiaQuerySet)):
    def get_queryset(self):
        return super().get_queryset().com_relacionamentos()


class Noticia(ModeloBase):
    titulo = models.CharField("titulo", max_length=200)
    subtitulo = models.CharField("subtitulo", max_length=300, blank=True)
    slug = models.SlugField("slug", max_length=220, unique=True, blank=True)
    resumo = models.TextField("resumo", max_length=500, blank=True)
    conteudo = models.TextField("conteudo")

    imagem_principal = models.ImageField(
        "imagem principal", upload_to="noticias/%Y/%m/", blank=True, null=True
    )
    imagem_url = models.URLField("imagem por URL", blank=True)
    imagem_legenda = models.CharField("legenda da imagem", max_length=250, blank=True)
    imagem_credito = models.CharField("credito da imagem", max_length=120, blank=True)

    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="noticias",
        verbose_name="autor",
    )
    categoria = models.ForeignKey(
        "categories.Categoria",
        on_delete=models.PROTECT,
        related_name="noticias",
        verbose_name="categoria",
    )
    tags = models.ManyToManyField(
        "categories.Tag", blank=True, related_name="noticias", verbose_name="tags"
    )

    status = models.CharField(
        "status", max_length=10, choices=StatusNoticia.choices,
        default=StatusNoticia.RASCUNHO, db_index=True,
    )
    formato = models.CharField(
        "formato", max_length=12, choices=FormatoNoticia.choices,
        default=FormatoNoticia.TEXTO,
    )
    destaque = models.BooleanField("destaque na home", default=False, db_index=True)
    breaking_news = models.BooleanField("urgente", default=False, db_index=True)
    exclusivo = models.BooleanField("conteudo exclusivo", default=False)
    permitir_comentarios = models.BooleanField("permitir comentarios", default=True)

    visualizacoes = models.PositiveIntegerField("visualizacoes", default=0, db_index=True)
    tempo_leitura = models.PositiveSmallIntegerField("tempo de leitura (min)", default=1)

    data_publicacao = models.DateTimeField("data de publicacao", db_index=True,
                                           blank=True, null=True)
    data_atualizacao = models.DateTimeField("ultima atualizacao editorial",
                                            blank=True, null=True)

    objects = NoticiaManager()

    class Meta:
        verbose_name = "noticia"
        verbose_name_plural = "noticias"
        ordering = ["-data_publicacao", "-criado_em"]
        indexes = [
            models.Index(fields=["status", "-data_publicacao"]),
            models.Index(fields=["categoria", "-data_publicacao"]),
        ]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slug_unico(Noticia, self.titulo, self)
        if not self.resumo:
            self.resumo = texto_puro(self.conteudo)[:280]
        self.tempo_leitura = calcular_tempo_leitura(self.conteudo)
        if self.status == StatusNoticia.PUBLICADA and not self.data_publicacao:
            self.data_publicacao = timezone.now()
        if self.pk:
            self.data_atualizacao = timezone.now()
        super().save(*args, **kwargs)

    @property
    def esta_publicada(self):
        return (
            self.status == StatusNoticia.PUBLICADA
            and self.data_publicacao is not None
            and self.data_publicacao <= timezone.now()
        )

    @property
    def capa(self):
        if self.imagem_principal:
            return self.imagem_principal.url
        return self.imagem_url or ""


class Fonte(models.Model):
    """Fontes citadas na materia (credibilidade editorial)."""

    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE, related_name="fontes")
    titulo = models.CharField("titulo", max_length=160)
    url = models.URLField("url", blank=True)

    class Meta:
        verbose_name = "fonte"
        verbose_name_plural = "fontes"

    def __str__(self):
        return self.titulo


class Midia(models.Model):
    """Conteudo multimidia anexado a uma noticia."""

    class Tipo(models.TextChoices):
        IMAGEM = "IMAGEM", "Imagem"
        GALERIA = "GALERIA", "Item de galeria"
        VIDEO = "VIDEO", "Video"
        AUDIO = "AUDIO", "Audio"
        PODCAST = "PODCAST", "Podcast"
        INFOGRAFICO = "INFOGRAFICO", "Infografico"

    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE, related_name="midias")
    tipo = models.CharField("tipo", max_length=12, choices=Tipo.choices)
    arquivo = models.FileField("arquivo", upload_to="midias/%Y/%m/", blank=True, null=True)
    url = models.URLField("url externa", blank=True)
    legenda = models.CharField("legenda", max_length=250, blank=True)
    credito = models.CharField("credito", max_length=120, blank=True)
    ordem = models.PositiveSmallIntegerField("ordem", default=0)

    class Meta:
        verbose_name = "midia"
        verbose_name_plural = "midias"
        ordering = ["ordem", "id"]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.noticia.titulo}"


class CoberturaAoVivo(ModeloBase):
    class Status(models.TextChoices):
        AO_VIVO = "AO_VIVO", "Ao vivo"
        PAUSADA = "PAUSADA", "Pausada"
        ENCERRADA = "ENCERRADA", "Encerrada"

    titulo = models.CharField("titulo", max_length=200)
    slug = models.SlugField("slug", max_length=220, unique=True, blank=True)
    resumo = models.TextField("resumo", max_length=400, blank=True)
    categoria = models.ForeignKey(
        "categories.Categoria", on_delete=models.PROTECT, related_name="coberturas"
    )
    noticia = models.ForeignKey(
        Noticia, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="coberturas", verbose_name="materia relacionada",
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="coberturas"
    )
    status = models.CharField("status", max_length=10, choices=Status.choices,
                              default=Status.AO_VIVO, db_index=True)
    iniciada_em = models.DateTimeField("iniciada em", default=timezone.now)
    encerrada_em = models.DateTimeField("encerrada em", blank=True, null=True)

    class Meta:
        verbose_name = "cobertura ao vivo"
        verbose_name_plural = "coberturas ao vivo"
        ordering = ["-iniciada_em"]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slug_unico(CoberturaAoVivo, self.titulo, self)
        if self.status == self.Status.ENCERRADA and not self.encerrada_em:
            self.encerrada_em = timezone.now()
        super().save(*args, **kwargs)


class AtualizacaoAoVivo(models.Model):
    cobertura = models.ForeignKey(
        CoberturaAoVivo, on_delete=models.CASCADE, related_name="atualizacoes"
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="atualizacoes_ao_vivo"
    )
    titulo = models.CharField("titulo", max_length=180, blank=True)
    conteudo = models.TextField("conteudo")
    importante = models.BooleanField("destacar", default=False)
    horario = models.DateTimeField("horario", default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "atualizacao ao vivo"
        verbose_name_plural = "atualizacoes ao vivo"
        ordering = ["-horario"]

    def __str__(self):
        return f"{self.horario:%H:%M} - {self.cobertura.titulo}"


class Video(ModeloBase):
    class Plataforma(models.TextChoices):
        INTERNO = "INTERNO", "Arquivo interno"
        YOUTUBE = "YOUTUBE", "YouTube"
        VIMEO = "VIMEO", "Vimeo"
        OUTRA = "OUTRA", "Outra"

    titulo = models.CharField("titulo", max_length=200)
    slug = models.SlugField("slug", max_length=220, unique=True, blank=True)
    descricao = models.TextField("descricao", blank=True)
    categoria = models.ForeignKey(
        "categories.Categoria", on_delete=models.PROTECT, related_name="videos"
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="videos"
    )
    plataforma = models.CharField("plataforma", max_length=8,
                                  choices=Plataforma.choices, default=Plataforma.YOUTUBE)
    url = models.URLField("url do video", blank=True)
    id_externo = models.CharField("id na plataforma", max_length=60, blank=True)
    arquivo = models.FileField("arquivo", upload_to="videos/%Y/%m/", blank=True, null=True)
    thumbnail = models.ImageField("capa", upload_to="videos/capas/", blank=True, null=True)
    thumbnail_url = models.URLField("capa por URL", blank=True)
    duracao_segundos = models.PositiveIntegerField("duracao (s)", default=0)
    visualizacoes = models.PositiveIntegerField("visualizacoes", default=0)
    publicado = models.BooleanField("publicado", default=True, db_index=True)
    publicado_em = models.DateTimeField("publicado em", default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "video"
        verbose_name_plural = "videos"
        ordering = ["-publicado_em"]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slug_unico(Video, self.titulo, self)
        super().save(*args, **kwargs)


class Anuncio(ModeloBase):
    class Posicao(models.TextChoices):
        TOPO = "TOPO", "Banner do topo"
        LATERAL = "LATERAL", "Coluna lateral"
        MATERIA = "MATERIA", "Dentro da materia"
        FEED = "FEED", "Entre as noticias do feed"

    titulo = models.CharField("titulo", max_length=120)
    posicao = models.CharField("posicao", max_length=8, choices=Posicao.choices, db_index=True)
    imagem = models.ImageField("imagem", upload_to="anuncios/", blank=True, null=True)
    imagem_url = models.URLField("imagem por URL", blank=True)
    url_destino = models.URLField("link de destino")
    anunciante = models.CharField("anunciante", max_length=120, blank=True)
    ativo = models.BooleanField("ativo", default=True, db_index=True)
    inicio = models.DateTimeField("inicio", default=timezone.now)
    fim = models.DateTimeField("fim", blank=True, null=True)
    impressoes = models.PositiveIntegerField("impressoes", default=0)
    cliques = models.PositiveIntegerField("cliques", default=0)

    class Meta:
        verbose_name = "anuncio"
        verbose_name_plural = "anuncios"
        ordering = ["posicao", "-criado_em"]

    def __str__(self):
        return f"{self.titulo} ({self.get_posicao_display()})"

    @property
    def vigente(self):
        agora = timezone.now()
        return self.ativo and self.inicio <= agora and (self.fim is None or self.fim >= agora)
