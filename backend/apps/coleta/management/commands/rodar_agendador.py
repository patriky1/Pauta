"""Agendador simples, SEM Redis e SEM Celery: roda a coleta a cada 40 minutos.

    python manage.py rodar_agendador                 # intervalo = COLETA_INTERVALO_MINUTOS
    python manage.py rodar_agendador --intervalo 10  # a cada 10 minutos (para testar)

Pensado para o Windows de desenvolvimento, onde instalar o Redis e abrir worker + beat e
trabalhoso. Deixe este comando aberto num terminal (ao lado do runserver): ele coleta ao
iniciar e depois a cada intervalo, executando exatamente o mesmo codigo de
`manage.py coletar_noticias` (mesma trava, mesmos logs, mesma deduplicacao).

Em producao prefira o Celery Beat (docker-compose.yml ou deploy/systemd/).
Rode UM so agendador: se houver mais de um (ou o beat do Celery junto), a trava garante
que so uma coleta ocorre por vez, mas as outras sao descartadas.
"""
import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import close_old_connections

from apps.coleta.services import sincronizar_todas

logger = logging.getLogger("apps.coleta")


class Command(BaseCommand):
    help = "Coleta noticias a cada COLETA_INTERVALO_MINUTOS, sem precisar de Redis/Celery."

    def add_arguments(self, parser):
        parser.add_argument("--intervalo", type=float, default=None,
                            help="Minutos entre coletas (padrao: COLETA_INTERVALO_MINUTOS).")

    def dormir(self, segundos):  # separado para os testes nao esperarem de verdade
        time.sleep(segundos)

    def rodada(self):
        """Uma coleta. Qualquer erro e registrado e o agendador continua vivo."""
        close_old_connections()
        try:
            resumo = sincronizar_todas()
        except Exception:
            logger.exception("Falha inesperada na coleta agendada; tentara de novo no proximo ciclo.")
            return
        if not resumo["executada"]:
            logger.warning("Coleta agendada pulada: %s", resumo["motivo"])

    def handle(self, *args, **opcoes):
        minutos = opcoes["intervalo"] or float(settings.COLETA_INTERVALO_MINUTOS)
        if minutos <= 0:
            raise ValueError("O intervalo precisa ser maior que zero.")
        self.stdout.write(self.style.SUCCESS(
            f"Agendador ativo: coleta ao iniciar e a cada {minutos:g} min. Ctrl+C para parar."))
        try:
            while True:
                inicio = time.monotonic()
                self.rodada()
                restante = max(minutos * 60 - (time.monotonic() - inicio), 1)
                logger.info("Proxima coleta em %.0f min.", restante / 60)
                self.dormir(restante)
        except KeyboardInterrupt:
            self.stdout.write("\nAgendador encerrado.")
