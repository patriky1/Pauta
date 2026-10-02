"""Tarefas do Celery. O agendamento (a cada 40 min) fica em CELERY_BEAT_SCHEDULE no settings.

A tarefa periodica executa o comando `manage.py coletar_noticias` (via call_command, no
proprio processo do worker), entao a coleta agendada e a manual sao exatamente a mesma.
"""
import io
import logging

from celery import shared_task

logger = logging.getLogger("apps.coleta")


@shared_task(name="apps.coleta.tasks.coletar_noticias", ignore_result=True)
def coletar_noticias():
    """Executada pelo Celery Beat: roda `manage.py coletar_noticias` (todas as fontes ativas)."""
    from django.core.management import call_command
    from django.core.management.base import CommandError

    from .management.commands.coletar_noticias import Command

    comando = Command()
    saida = io.StringIO()
    try:
        call_command(comando, stdout=saida, stderr=saida)
    except CommandError as erro:
        if comando.resumo is not None and not comando.resumo["executada"]:
            # outra coleta em andamento: a trava fez o trabalho dela, nada a fazer
            logger.warning("Coleta agendada pulada: %s", erro)
            return comando.resumo
        raise
    resumo = dict(comando.resumo)
    resumo.pop("detalhes", None)
    return resumo


@shared_task(name="apps.coleta.tasks.sincronizar_fonte", ignore_result=True)
def sincronizar_fonte_tarefa(fonte_id):
    """Sincroniza uma unica fonte em segundo plano (respeita a trava global)."""
    from .models import FonteNoticia
    from .services import sincronizar_fonte_exclusiva

    fonte = FonteNoticia.objects.filter(pk=fonte_id).select_related("categoria_padrao").first()
    if fonte is None:
        logger.warning("Fonte %s nao existe mais.", fonte_id)
        return None
    execucao = sincronizar_fonte_exclusiva(fonte)
    return execucao.status if execucao else None
