"""Corrige a imagem de notícias já importadas que ficaram com o logo da fonte.

    python manage.py coleta_reparar_imagens
    python manage.py coleta_reparar_imagens --fonte agencia-brasil

O que faz, para cada fonte:
  1. lê o feed de novo e troca o logo/imagem genérica pela foto real da matéria;
  2. nas notícias que já saíram do feed (e por isso não têm foto para recuperar),
     apenas remove o logo, para ele não aparecer como se fosse a foto da matéria.

Notícias com foto de verdade não são tocadas.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from apps.coleta.cliente import ErroColeta
from apps.coleta.models import FonteNoticia
from apps.coleta.parser import ErroFeed
from apps.coleta.services import indexar_existentes, obter_itens, preparar
from apps.coleta.texto import imagem_util
from apps.news.models import Noticia
from apps.news.services import invalidar_carrossel


class Command(BaseCommand):
    help = "Troca logos e imagens genéricas de notícias importadas pela foto real do feed."

    def add_arguments(self, parser):
        parser.add_argument("--fonte", action="append", default=[],
                            help="Slug ou id da fonte (pode repetir). Padrão: todas.")

    def handle(self, *args, **opcoes):
        fontes = FonteNoticia.objects.select_related("categoria_padrao")
        if opcoes["fonte"]:
            filtro = Q()
            for valor in opcoes["fonte"]:
                filtro |= Q(slug=valor) | (Q(pk=int(valor)) if valor.isdigit() else Q())
            fontes = fontes.filter(filtro)
        fontes = list(fontes)
        if not fontes:
            raise CommandError("Nenhuma fonte encontrada.")

        trocadas = removidas = 0
        for fonte in fontes:
            # ignora o cache (ETag) só nesta execução, sem gravar na fonte
            fonte.etag = ""
            fonte.ultima_modificacao = ""
            try:
                itens, _ = obter_itens(fonte)
            except (ErroColeta, ErroFeed) as erro:
                self.stdout.write(self.style.WARNING(f"{fonte.nome}: não foi possível ler o feed ({erro})"))
                itens = []

            preparados = [p for p in (preparar(fonte, item) for item in itens) if p]
            indice = indexar_existentes(fonte, preparados)
            for preparado in preparados:
                noticia = indice.buscar(fonte, preparado)
                if noticia is None or noticia.fonte_externa_id != fonte.pk or not preparado.imagem:
                    continue
                atual = noticia.imagem_url or ""
                if atual == preparado.imagem or (atual and imagem_util(atual)):
                    continue  # já tem foto de verdade
                noticia.imagem_url = preparado.imagem
                noticia.imagem_credito = f"Imagem: {fonte.nome}"[:120]
                noticia.save(update_fields=["imagem_url", "imagem_credito"])
                trocadas += 1

            # o que sobrou com logo e não está mais no feed: remove o logo
            for noticia in Noticia.objects.select_related(None).prefetch_related(None).filter(
                fonte_externa=fonte
            ).exclude(imagem_url=""):
                if not imagem_util(noticia.imagem_url):
                    noticia.imagem_url = ""
                    noticia.imagem_credito = ""
                    noticia.save(update_fields=["imagem_url", "imagem_credito"])
                    removidas += 1

            self.stdout.write(f"{fonte.nome}: ok")

        invalidar_carrossel()
        self.stdout.write(self.style.SUCCESS(
            f"Pronto: {trocadas} foto(s) recuperada(s), {removidas} logo(s) removido(s)."
        ))
