from django.contrib import admin

from .models import (
    Anuncio,
    AtualizacaoAoVivo,
    CoberturaAoVivo,
    Fonte,
    Midia,
    Noticia,
    Video,
)


class FonteInline(admin.TabularInline):
    model = Fonte
    extra = 1


class MidiaInline(admin.TabularInline):
    model = Midia
    extra = 1


@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "autor", "status", "destaque",
                    "breaking_news", "visualizacoes", "data_publicacao")
    list_filter = ("status", "categoria", "destaque", "breaking_news", "exclusivo")
    search_fields = ("titulo", "subtitulo", "resumo", "conteudo")
    autocomplete_fields = ("autor", "categoria", "tags")
    prepopulated_fields = {"slug": ("titulo",)}
    date_hierarchy = "data_publicacao"
    inlines = [FonteInline, MidiaInline]
    readonly_fields = ("visualizacoes", "tempo_leitura", "criado_em", "atualizado_em")


class AtualizacaoInline(admin.TabularInline):
    model = AtualizacaoAoVivo
    extra = 1


@admin.register(CoberturaAoVivo)
class CoberturaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "status", "iniciada_em")
    list_filter = ("status", "categoria")
    search_fields = ("titulo",)
    inlines = [AtualizacaoInline]


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "plataforma", "publicado", "publicado_em")
    list_filter = ("plataforma", "publicado", "categoria")
    search_fields = ("titulo", "descricao")


@admin.register(Anuncio)
class AnuncioAdmin(admin.ModelAdmin):
    list_display = ("titulo", "anunciante", "posicao", "ativo", "impressoes", "cliques")
    list_filter = ("posicao", "ativo")
    search_fields = ("titulo", "anunciante")
