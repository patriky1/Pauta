from django.contrib import admin

from .models import Evento


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ("tipo", "noticia", "usuario", "criado_em")
    list_filter = ("tipo",)
