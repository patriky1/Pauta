from django.contrib import admin

from .models import Comentario, CurtidaComentario, Denuncia


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ("autor", "noticia", "status", "criado_em")
    list_filter = ("status",)
    search_fields = ("conteudo", "autor__username")


admin.site.register(CurtidaComentario)
admin.site.register(Denuncia)
