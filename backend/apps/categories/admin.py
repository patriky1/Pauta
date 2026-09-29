from django.contrib import admin

from .models import Categoria, Tag


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug", "cor", "ordem", "ativa")
    list_editable = ("ordem", "ativa")
    search_fields = ("nome",)
    prepopulated_fields = {"slug": ("nome",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug")
    search_fields = ("nome",)
    prepopulated_fields = {"slug": ("nome",)}
