"""Cadastra as fontes brasileiras confiaveis do catalogo (apps/coleta/fontes_brasil.py).

    python manage.py coleta_fontes              # cria as que faltam, ja ATIVAS
    python manage.py coleta_fontes --inativas   # cria desligadas (ative no /django-admin/)
    python manage.py coleta_fontes --listar     # so mostra o catalogo e o que ja existe

Idempotente: fontes ja cadastradas (mesma URL do feed) nao sao alteradas, entao uma
fonte que voce desativou ou editou no painel continua do jeito que voce deixou.
Precisa de categorias cadastradas (rode `seed_data` ou crie pelo painel).
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from apps.categories.models import Categoria
from apps.coleta.fontes_brasil import FONTES_BRASILEIRAS
from apps.coleta.models import FonteNoticia
from apps.coleta.texto import normalizar_texto


class Command(BaseCommand):
    help = "Cadastra fontes brasileiras confiaveis (RSS) para a coleta automatica."

    def add_arguments(self, parser):
        parser.add_argument("--inativas", action="store_true",
                            help="Cria as fontes desligadas.")
        parser.add_argument("--listar", action="store_true",
                            help="Apenas lista o catalogo, sem gravar nada.")

    def handle(self, *args, **opcoes):
        existentes = set(FonteNoticia.objects.values_list("url_feed", flat=True))
        if opcoes["listar"]:
            for nome, url, _, categoria in FONTES_BRASILEIRAS:
                marca = "cadastrada" if url in existentes else "nova"
                self.stdout.write(f"[{marca:10}] {nome} ({categoria}) — {url}")
            return

        categorias = {}
        for categoria in Categoria.objects.all():
            categorias[normalizar_texto(categoria.nome)] = categoria
            categorias[normalizar_texto(categoria.slug)] = categoria
        if not categorias:
            raise CommandError("Cadastre as categorias primeiro (ou rode seed_data).")
        padrao = categorias.get("brasil") or Categoria.objects.filter(ativa=True).first() \
            or Categoria.objects.first()

        criadas = ja_existiam = 0
        for nome, url, site, chave in FONTES_BRASILEIRAS:
            if url in existentes:
                ja_existiam += 1
                continue
            if FonteNoticia.objects.filter(nome=nome).exists():
                self.stdout.write(self.style.WARNING(
                    f"Ja existe uma fonte chamada '{nome}' com outra URL; mantida como esta."))
                ja_existiam += 1
                continue
            try:
                with transaction.atomic():
                    FonteNoticia.objects.create(
                        nome=nome, url_feed=url, url_site=site, tipo=FonteNoticia.Tipo.RSS,
                        categoria_padrao=categorias.get(chave) or padrao,
                        ativa=not opcoes["inativas"],
                        publicar_automaticamente=True,
                        importar_conteudo_completo=False,
                        buscar_imagem_na_pagina=False,
                    )
            except IntegrityError:  # criada em paralelo por outro processo
                ja_existiam += 1
                continue
            criadas += 1
            self.stdout.write(f"+ {nome}")

        situacao = "inativa(s)" if opcoes["inativas"] else "ativa(s)"
        self.stdout.write(self.style.SUCCESS(
            f"{criadas} fonte(s) {situacao} criada(s); {ja_existiam} ja existia(m)."))
