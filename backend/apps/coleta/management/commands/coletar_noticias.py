"""Executa a coleta de noticias. E o MESMO comando que o Celery Beat dispara a cada 40 min.

    python manage.py coletar_noticias                 # todas as fontes ativas
    python manage.py coletar_noticias --fonte agencia-brasil --fonte 3
    python manage.py coletar_noticias --em-segundo-plano   # envia para o Celery

Fluxo: agendador -> este comando -> fontes -> validacao/deduplicacao -> banco -> API -> React.
"""
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from apps.coleta.models import FonteNoticia
from apps.coleta.services import sincronizar_todas

logger = logging.getLogger("apps.coleta")


class Command(BaseCommand):
    help = "Busca noticias nas fontes externas cadastradas."

    # resumo da ultima execucao (lido pela tarefa do Celery que chama este comando)
    resumo = None

    def add_arguments(self, parser):
        parser.add_argument("--fonte", action="append", default=[],
                            help="Slug ou id da fonte (pode repetir). Aceita fontes inativas.")
        parser.add_argument("--em-segundo-plano", action="store_true",
                            help="Enfileira a tarefa no Celery em vez de rodar aqui.")

    def handle(self, *args, **opcoes):
        if opcoes["em_segundo_plano"]:
            from apps.coleta.tasks import coletar_noticias

            coletar_noticias.delay()
            self.stdout.write(self.style.SUCCESS("Coleta enviada para o Celery."))
            return

        fontes = None
        if opcoes["fonte"]:
            filtro = Q()
            for valor in opcoes["fonte"]:
                filtro |= Q(slug=valor) | (Q(pk=int(valor)) if valor.isdigit() else Q())
            fontes = list(FonteNoticia.objects.filter(filtro).select_related("categoria_padrao"))
            if not fontes:
                raise CommandError("Nenhuma fonte encontrada com os valores informados.")

        resumo = self.resumo = sincronizar_todas(fontes)
        if not resumo["executada"]:
            raise CommandError(resumo["motivo"])
        for item in resumo["detalhes"]:
            estilo = self.style.ERROR if item["status"] == "ERRO" else self.style.SUCCESS
            self.stdout.write(estilo(
                f"{item['fonte']}: {item['status']} — novas {item['novas']}, "
                f"atualizadas {item['atualizadas']}, ignoradas {item['ignoradas']}"
            ))
            if item["mensagem"]:
                self.stdout.write(f"   {item['mensagem'][:300]}")
        self.stdout.write(
            f"Total: {resumo['fontes']} fonte(s), {resumo['novas']} nova(s), "
            f"{resumo['erros']} com erro."
        )
