from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html

from .models import ExecucaoColeta, FonteNoticia, MapeamentoCategoria, RegraCategorizacao


class MapeamentoInline(admin.TabularInline):
    model = MapeamentoCategoria
    extra = 1
    autocomplete_fields = ("categoria",)


@admin.register(FonteNoticia)
class FonteNoticiaAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "ativa", "categoria_padrao", "situacao",
                    "ultima_sincronizacao", "total_importadas", "ver_execucoes")
    list_filter = ("ativa", "tipo", "categoria_padrao", "publicar_automaticamente")
    list_editable = ("ativa",)
    search_fields = ("nome", "url_feed", "url_site")
    prepopulated_fields = {"slug": ("nome",)}
    autocomplete_fields = ("categoria_padrao",)
    list_select_related = ("categoria_padrao",)
    inlines = [MapeamentoInline]
    actions = ("sincronizar_agora", "ativar", "desativar", "zerar_erros")
    readonly_fields = ("ultima_sincronizacao", "ultimo_sucesso", "ultimo_erro",
                       "erros_consecutivos", "total_importadas", "etag", "ultima_modificacao",
                       "criado_em", "atualizado_em")
    fieldsets = (
        (None, {"fields": ("nome", "slug", "url_site", "url_feed", "tipo", "ativa",
                           "categoria_padrao")}),
        ("Publicação", {"fields": ("publicar_automaticamente", "importar_conteudo_completo",
                                   "buscar_imagem_na_pagina", "limite_por_coleta")}),
        ("API JSON (opcional)", {
            "classes": ("collapse",),
            "fields": ("mapeamento_json", "chave_api_variavel", "chave_api_parametro"),
        }),
        ("Última sincronização", {"fields": readonly_fields}),
    )

    @admin.display(description="situação")
    def situacao(self, obj):
        if not obj.ultima_sincronizacao:
            return "—"
        if obj.erros_consecutivos:
            return format_html('<span style="color:#b91c1c" title="{}">erro ({}x)</span>',
                               obj.ultimo_erro[:300], obj.erros_consecutivos)
        if obj.ultimo_erro:
            return format_html('<span style="color:#a16207" title="{}">parcial</span>',
                               obj.ultimo_erro[:300])
        return format_html('<span style="color:#0f7b52">ok</span>')

    @admin.display(description="log")
    def ver_execucoes(self, obj):
        url = reverse("admin:coleta_execucaocoleta_changelist") + f"?fonte__id__exact={obj.pk}"
        return format_html('<a href="{}">execuções</a>', url)

    @admin.action(description="Sincronizar agora")
    def sincronizar_agora(self, request, queryset):
        from .services import sincronizar_fonte

        for fonte in queryset.select_related("categoria_padrao"):
            execucao = sincronizar_fonte(fonte)
            nivel = messages.ERROR if execucao.status == "ERRO" else messages.SUCCESS
            self.message_user(
                request,
                f"{fonte.nome}: {execucao.get_status_display()} — {execucao.novas} nova(s), "
                f"{execucao.atualizadas} atualizada(s), {execucao.ignoradas} ignorada(s). "
                f"{execucao.mensagem[:200]}",
                nivel,
            )

    @admin.action(description="Ativar")
    def ativar(self, request, queryset):
        queryset.update(ativa=True)

    @admin.action(description="Desativar")
    def desativar(self, request, queryset):
        queryset.update(ativa=False)

    @admin.action(description="Zerar contador de erros")
    def zerar_erros(self, request, queryset):
        queryset.update(erros_consecutivos=0, ultimo_erro="")


@admin.register(MapeamentoCategoria)
class MapeamentoCategoriaAdmin(admin.ModelAdmin):
    list_display = ("termo_origem", "categoria", "fonte")
    list_filter = ("fonte", "categoria")
    search_fields = ("termo_origem",)
    autocomplete_fields = ("categoria", "fonte")


@admin.register(RegraCategorizacao)
class RegraCategorizacaoAdmin(admin.ModelAdmin):
    list_display = ("categoria", "resumo_palavras", "peso", "ativa")
    list_editable = ("peso", "ativa")
    list_filter = ("ativa", "categoria")
    autocomplete_fields = ("categoria",)

    @admin.display(description="palavras-chave")
    def resumo_palavras(self, obj):
        return obj.palavras_chave[:90]


@admin.register(ExecucaoColeta)
class ExecucaoColetaAdmin(admin.ModelAdmin):
    list_display = ("fonte", "status", "iniciada_em", "duracao_segundos", "itens_lidos",
                    "novas", "atualizadas", "ignoradas")
    list_filter = ("status", "fonte")
    date_hierarchy = "iniciada_em"
    list_select_related = ("fonte",)
    readonly_fields = [campo.name for campo in ExecucaoColeta._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
