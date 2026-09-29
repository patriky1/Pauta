import io
from datetime import timedelta

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase

from apps.coleta.tasks import coletar_noticias, sincronizar_fonte_tarefa
from apps.news.models import Noticia

from . import amostras
from .base import BaseColeta, resposta


class AgendamentoTests(SimpleTestCase):
    def test_beat_agenda_a_cada_40_minutos(self):
        agendamento = settings.CELERY_BEAT_SCHEDULE["coletar-noticias"]
        self.assertEqual(agendamento["task"], "apps.coleta.tasks.coletar_noticias")
        self.assertEqual(agendamento["schedule"],
                         timedelta(minutes=settings.COLETA_INTERVALO_MINUTOS))

    def test_intervalo_padrao_e_40_minutos(self):
        import os

        if "COLETA_INTERVALO_MINUTOS" in os.environ:
            self.skipTest("Intervalo sobrescrito pelo .env")
        self.assertEqual(settings.COLETA_INTERVALO_MINUTOS, 40)

    def test_tarefa_registrada_na_app_celery(self):
        from config.celery import app

        app.loader.import_default_modules()
        self.assertIn("apps.coleta.tasks.coletar_noticias", app.tasks)


class TarefaTests(BaseColeta):
    def test_tarefa_periodica_coleta(self):
        with self.baixar_retornando(resposta(amostras.RSS)):
            resumo = coletar_noticias.apply().get()
        self.assertEqual(resumo["novas"], 3)
        self.assertEqual(Noticia.objects.count(), 3)

    def test_tarefa_de_uma_fonte(self):
        with self.baixar_retornando(resposta(amostras.RSS)):
            situacao = sincronizar_fonte_tarefa.apply(args=[self.fonte.pk]).get()
        self.assertEqual(situacao, "SUCESSO")
        self.assertIsNone(sincronizar_fonte_tarefa.apply(args=[999999]).get())

    def test_comando_manual(self):
        saida = io.StringIO()
        with self.baixar_retornando(resposta(amostras.RSS)):
            call_command("coletar_noticias", "--fonte", self.fonte.slug, stdout=saida)
        self.assertIn("novas 3", saida.getvalue())
        self.assertEqual(Noticia.objects.count(), 3)

    def test_comando_exemplos_e_idempotente(self):
        from apps.coleta.models import FonteNoticia, RegraCategorizacao

        call_command("coleta_exemplos", stdout=io.StringIO())
        call_command("coleta_exemplos", stdout=io.StringIO())
        self.assertEqual(FonteNoticia.objects.filter(url_feed__contains="agenciabrasil").count(), 2)
        self.assertFalse(FonteNoticia.objects.get(url_feed__contains="ultimasnoticias").ativa)
        self.assertEqual(RegraCategorizacao.objects.filter(categoria=self.economia).count(), 1)
