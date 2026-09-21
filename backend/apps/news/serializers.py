from django.utils import timezone
from rest_framework import serializers

from apps.categories.models import Categoria, Tag
from apps.categories.serializers import CategoriaResumoSerializer, TagSerializer
from apps.users.serializers import UsuarioResumoSerializer

from .models import (
    Anuncio,
    AtualizacaoAoVivo,
    CoberturaAoVivo,
    Fonte,
    Midia,
    Noticia,
    StatusNoticia,
    Video,
)


def url_absoluta(contexto, caminho):
    if not caminho:
        return ""
    request = contexto.get("request")
    if request and caminho.startswith("/"):
        return request.build_absolute_uri(caminho)
    return caminho


class FonteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fonte
        fields = ("id", "titulo", "url")


class MidiaSerializer(serializers.ModelSerializer):
    arquivo_url = serializers.SerializerMethodField()

    class Meta:
        model = Midia
        fields = ("id", "tipo", "url", "arquivo_url", "legenda", "credito", "ordem")

    def get_arquivo_url(self, obj):
        return url_absoluta(self.context, obj.arquivo.url if obj.arquivo else "")


class NoticiaListaSerializer(serializers.ModelSerializer):
    autor = UsuarioResumoSerializer(read_only=True)
    categoria = CategoriaResumoSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    imagem = serializers.SerializerMethodField()
    favoritada = serializers.SerializerMethodField()

    class Meta:
        model = Noticia
        fields = (
            "id", "titulo", "subtitulo", "slug", "resumo", "imagem", "imagem_legenda",
            "imagem_credito", "autor", "categoria", "tags", "formato", "destaque",
            "breaking_news", "exclusivo", "visualizacoes", "tempo_leitura",
            "data_publicacao", "data_atualizacao", "favoritada",
        )
        read_only_fields = fields

    def get_imagem(self, obj):
        return url_absoluta(self.context, obj.capa)

    def get_favoritada(self, obj):
        favoritos = self.context.get("favoritos")
        if favoritos is None:
            return False
        return obj.pk in favoritos


class NoticiaDetalheSerializer(NoticiaListaSerializer):
    fontes = FonteSerializer(many=True, read_only=True)
    midias = MidiaSerializer(many=True, read_only=True)
    relacionadas = serializers.SerializerMethodField()
    total_comentarios = serializers.SerializerMethodField()
    cobertura_ao_vivo = serializers.SerializerMethodField()

    class Meta(NoticiaListaSerializer.Meta):
        fields = NoticiaListaSerializer.Meta.fields + (
            "conteudo", "status", "permitir_comentarios", "fontes", "midias",
            "relacionadas", "total_comentarios", "cobertura_ao_vivo",
        )
        read_only_fields = fields

    def get_relacionadas(self, obj):
        consulta = (
            Noticia.objects.publicadas()
            .filter(categoria=obj.categoria)
            .exclude(pk=obj.pk)
            .order_by("-data_publicacao")[:4]
        )
        return NoticiaListaSerializer(consulta, many=True, context=self.context).data

    def get_total_comentarios(self, obj):
        return obj.comentarios.filter(status="PUBLICADO").count()

    def get_cobertura_ao_vivo(self, obj):
        cobertura = obj.coberturas.filter(status="AO_VIVO").first()
        if not cobertura:
            return None
        return {"id": cobertura.id, "slug": cobertura.slug, "titulo": cobertura.titulo}


class NoticiaEscritaSerializer(serializers.ModelSerializer):
    """Criacao/edicao pela redacao e pelo painel administrativo."""

    categoria_id = serializers.PrimaryKeyRelatedField(
        source="categoria", queryset=Categoria.objects.all()
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50), required=False, write_only=True
    )
    fontes = FonteSerializer(many=True, required=False)

    class Meta:
        model = Noticia
        fields = (
            "id", "titulo", "subtitulo", "slug", "resumo", "conteudo",
            "imagem_principal", "imagem_url", "imagem_legenda", "imagem_credito",
            "categoria_id", "tags", "fontes", "status", "formato", "destaque",
            "breaking_news", "exclusivo", "permitir_comentarios", "data_publicacao",
        )
        read_only_fields = ("id", "slug")

    def validate(self, dados):
        status_novo = dados.get("status", getattr(self.instance, "status", None))
        publicacao = dados.get("data_publicacao", getattr(self.instance, "data_publicacao", None))
        if status_novo == StatusNoticia.AGENDADA:
            if not publicacao:
                raise serializers.ValidationError(
                    {"data_publicacao": "Informe a data para agendar a publicacao."}
                )
            if publicacao <= timezone.now():
                raise serializers.ValidationError(
                    {"data_publicacao": "A data agendada precisa estar no futuro."}
                )
        return dados

    def _sincronizar(self, noticia, tags, fontes):
        if tags is not None:
            objetos = []
            for nome in tags:
                nome = nome.strip()
                if not nome:
                    continue
                tag, _ = Tag.objects.get_or_create(nome__iexact=nome, defaults={"nome": nome})
                objetos.append(tag)
            noticia.tags.set(objetos)
        if fontes is not None:
            noticia.fontes.all().delete()
            Fonte.objects.bulk_create(
                [Fonte(noticia=noticia, **fonte) for fonte in fontes]
            )

    def create(self, dados):
        tags = dados.pop("tags", [])
        fontes = dados.pop("fontes", [])
        dados["autor"] = self.context["request"].user
        noticia = Noticia.objects.create(**dados)
        self._sincronizar(noticia, tags, fontes)
        return noticia

    def update(self, instancia, dados):
        tags = dados.pop("tags", None)
        fontes = dados.pop("fontes", None)
        for campo, valor in dados.items():
            setattr(instancia, campo, valor)
        instancia.save()
        self._sincronizar(instancia, tags, fontes)
        return instancia

    def to_representation(self, instancia):
        return NoticiaDetalheSerializer(instancia, context=self.context).data


class AtualizacaoAoVivoSerializer(serializers.ModelSerializer):
    autor = UsuarioResumoSerializer(read_only=True)

    class Meta:
        model = AtualizacaoAoVivo
        fields = ("id", "titulo", "conteudo", "importante", "horario", "autor", "cobertura")
        read_only_fields = ("id", "autor")


class CoberturaAoVivoSerializer(serializers.ModelSerializer):
    categoria = CategoriaResumoSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        source="categoria", queryset=Categoria.objects.all(), write_only=True
    )
    criado_por = UsuarioResumoSerializer(read_only=True)
    atualizacoes = AtualizacaoAoVivoSerializer(many=True, read_only=True)
    total_atualizacoes = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = CoberturaAoVivo
        fields = (
            "id", "titulo", "slug", "resumo", "status", "categoria", "categoria_id",
            "criado_por", "iniciada_em", "encerrada_em", "atualizacoes",
            "total_atualizacoes", "noticia",
        )
        read_only_fields = ("id", "slug", "criado_por", "encerrada_em")

    def create(self, dados):
        dados["criado_por"] = self.context["request"].user
        return super().create(dados)


class CoberturaResumoSerializer(serializers.ModelSerializer):
    categoria = CategoriaResumoSerializer(read_only=True)
    ultima_atualizacao = serializers.SerializerMethodField()

    class Meta:
        model = CoberturaAoVivo
        fields = ("id", "titulo", "slug", "resumo", "status", "categoria",
                  "iniciada_em", "ultima_atualizacao")

    def get_ultima_atualizacao(self, obj):
        atualizacao = obj.atualizacoes.first()
        if not atualizacao:
            return None
        return {
            "titulo": atualizacao.titulo,
            "conteudo": atualizacao.conteudo[:180],
            "horario": atualizacao.horario,
        }


class VideoSerializer(serializers.ModelSerializer):
    categoria = CategoriaResumoSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        source="categoria", queryset=Categoria.objects.all(), write_only=True
    )
    autor = UsuarioResumoSerializer(read_only=True)
    capa = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = (
            "id", "titulo", "slug", "descricao", "categoria", "categoria_id", "autor",
            "plataforma", "url", "id_externo", "capa", "thumbnail_url",
            "duracao_segundos", "visualizacoes", "publicado", "publicado_em",
        )
        read_only_fields = ("id", "slug", "autor", "visualizacoes")

    def get_capa(self, obj):
        caminho = obj.thumbnail.url if obj.thumbnail else obj.thumbnail_url
        return url_absoluta(self.context, caminho)

    def create(self, dados):
        dados["autor"] = self.context["request"].user
        return super().create(dados)


class AnuncioSerializer(serializers.ModelSerializer):
    imagem_final = serializers.SerializerMethodField()

    class Meta:
        model = Anuncio
        fields = (
            "id", "titulo", "posicao", "imagem", "imagem_url", "imagem_final",
            "url_destino", "anunciante", "ativo", "inicio", "fim",
            "impressoes", "cliques",
        )
        read_only_fields = ("id", "impressoes", "cliques")

    def get_imagem_final(self, obj):
        return url_absoluta(self.context, obj.imagem.url if obj.imagem else obj.imagem_url)
