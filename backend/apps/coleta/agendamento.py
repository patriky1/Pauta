"""Integracao da coleta com o Celery Beat.

O beat guarda a hora da ultima execucao em CELERY_BEAT_SCHEDULE_FILENAME. Depois de uma
reinicializacao ele mesmo dispara a coleta atrasada. O que ele nao cobre e o PRIMEIRO
start (ou um start sem esse arquivo, como num container recriado): nesse caso esperaria
40 minutos inteiros. `disparar_se_atrasada` cobre essa lacuna olhando o log da coleta.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.db.models import Max
from django.utils import timezone

logger = logging.getLogger("apps.coleta")

NOME_AGENDAMENTO = "coletar-noticias"


def intervalo():
    return timedelta(minutes=int(getattr(settings, "COLETA_INTERVALO_MINUTOS", 40)))


def coleta_atrasada(agora=None):
    """True se ha fonte ativa e nenhuma coleta comecou dentro do ultimo intervalo."""
    from .models import ExecucaoColeta, FonteNoticia

    if not FonteNoticia.objects.filter(ativa=True).exists():
        return False
    ultima = ExecucaoColeta.objects.aggregate(ultima=Max("iniciada_em"))["ultima"]
    agora = agora or timezone.now()
    return ultima is None or ultima <= agora - intervalo()


def beat_tem_historico(servico):
    """True se o beat ja executou a coleta antes (agenda persistida): ele cuida do atraso."""
    try:
        entrada = servico.scheduler.schedule.get(NOME_AGENDAMENTO)
    except Exception:  # agenda ilegivel: deixa a decisao para o log da coleta
        return False
    return bool(entrada is not None and entrada.total_run_count)


def disparar_se_atrasada(servico=None):
    """Chamado quando o beat inicia. Enfileira uma coleta imediata se estiver atrasada."""
    if not getattr(settings, "COLETA_EXECUTAR_AO_INICIAR", True):
        return False
    if servico is not None and beat_tem_historico(servico):
        return False
    if not coleta_atrasada():
        logger.info("Beat iniciado: coleta em dia; a proxima roda no horario agendado.")
        return False
    from .tasks import coletar_noticias

    segundos = int(intervalo().total_seconds())
    coletar_noticias.apply_async(expires=max(segundos - 60, 60))
    logger.info("Beat iniciado: coleta atrasada, enfileirada agora.")
    return True
