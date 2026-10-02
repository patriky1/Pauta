from django.contrib import admin

from .models import AutorSeguido, CategoriaSeguida, Favorito, Historico, TagSeguida

for modelo in (Favorito, Historico, CategoriaSeguida, AutorSeguido, TagSeguida):
    admin.site.register(modelo)
