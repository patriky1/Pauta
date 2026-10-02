"""Agendador (Celery Beat -> manage.py coletar_noticias), trava e fontes brasileiras."""
import io
import tempfile
import threading
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from apps.categories.models import Categoria
from apps.coleta import agendamento
from apps.coleta.fontes_brasil import FONTES_BRASILEIRAS
from apps.coleta.models import ExecucaoColeta, FonteNoticia
from apps.coleta.parser import ItemFeed
from apps.coleta.services import (
    preparar,
    sincronizar_fonte_exclusiva,
    sincronizar_todas,
)
from apps.coleta.tasks import coletar_noticias
from apps.coleta.trava import TravaArquivo, TravaCache, criar_trava, trava_coleta
from apps.news.models import Noticia
from apps.users.models import TipoUsuario, User

from . import amostras
from .base import BaseColeta, resposta


class OcupanteDaTrava:
    """Segura a trava numa OUTRA thread (= outra conexao/descritor), como faria um
    segundo processo, ate `soltar()`."""

    def __init__(self):
        self.pronta = threading.Event()
        self.liberar = threading.Event()
        self.obtida = None
        self.thread = threading.Thread(target=self._rodar, daemon=True)

    def _rodar(self):
        try:
            with trava_coleta() as obtida:
                self.obtida = obtida
                self.pronta.set()
                self.liberar.wait(10)
        finally:
            self.pronta.set()
            connection.close()  # conexao propria da thread

    def __enter__(self):
        self.thread.start()
        self.pronta.wait(10)
        return self

    def __exit__(self, *exc):
        self.liberar.set()
        self.thread.join(10)


class TravaTests(BaseColeta):
    def test_segunda_coleta_e_recusada_enquanto_outra_roda(self):
        with OcupanteDaTrava() as ocupante:
            self.assertTrue(ocupante.obtida)
            with self.baixar_retornando() as baixar:
                resumo = sincronizar_todas()
            self.assertFalse(resumo["executada"])
            baixar.assert_not_called()
        # liberada: agora roda normalmente
        with self.baixar_retornando(resposta(amostras.RSS)):
            self.assertTrue(sincronizar_todas()["executada"])

    def test_sincronizar_uma_fonte_tambem_respeita_a_trava(self):
        with OcupanteDaTrava():
            self.assertIsNone(sincronizar_fonte_exclusiva(self.fonte))
        self.assertFalse(ExecucaoColeta.objects.exists())

    def test_trava_liberada_mesmo_com_erro(self):
        with self.assertRaises(RuntimeError):
            with trava_coleta() as obtida:
                self.assertTrue(obtida)
                raise RuntimeError("falha no meio")
        with trava_coleta() as obtida:
            self.assertTrue(obtida)

    def test_auto_escolhe_pelo_banco(self):
        trava = criar_trava()
        esperado = "TravaBanco" if connection.vendor == "postgresql" else "TravaArquivo"
        self.assertEqual(type(trava).__name__, esperado)

    @override_settings(COLETA_TRAVA_BACKEND="inexistente")
    def test_backend_invalido_avisa(self):
        with self.assertRaises(ValueError):
            criar_trava()

    def test_comando_manual_falha_com_mensagem_clara_se_ocupado(self):
        with OcupanteDaTrava():
            with self.assertRaisesMessage(CommandError, "andamento"):
                call_command("coletar_noticias", stdout=io.StringIO())


class TravaArquivoTests(SimpleTestCase):
    def test_exclusiva_entre_descritores(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "sub" / "coleta.lock"
            primeira, segunda = TravaArquivo(caminho), TravaArquivo(caminho)
            self.assertTrue(primeira.adquirir())
            self.assertFalse(segunda.adquirir())
            primeira.liberar()
            self.assertTrue(segunda.adquirir())
            segunda.liberar()


class TravaCacheTests(SimpleTestCase):
    def test_nao_apaga_trava_de_outro_dono(self):
        from django.core.cache import cache

        from apps.coleta.trava import CHAVE_TRAVA

        cache.delete(CHAVE_TRAVA)
        primeira, segunda = TravaCache(), TravaCache()
        self.assertTrue(primeira.adquirir())
        self.assertFalse(segunda.adquirir())
        segunda.liberar()  # nao e dona: nao pode apagar
        self.assertEqual(cache.get(CHAVE_TRAVA), primeira.token)
        primeira.liberar()
        self.assertIsNone(cache.get(CHAVE_TRAVA))


class TarefaExecutaComandoTests(BaseColeta):
    def test_tarefa_roda_o_comando_coletar_noticias(self):
        from apps.coleta.management.commands import coletar_noticias as modulo

        with mock.patch.object(modulo.Command, "handle", autospec=True,
                               side_effect=modulo.Command.handle) as handle:
            with self.baixar_retornando(resposta(amostras.RSS)):
                resumo = coletar_noticias.apply().get()
        handle.assert_called_once()
        self.assertEqual(resumo["novas"], 3)
        self.assertNotIn("detalhes", resumo)

    def test_tarefa_com_coleta_em_andamento_nao_quebra(self):
        with OcupanteDaTrava():
            resumo = coletar_noticias.apply().get()
        self.assertFalse(resumo["executada"])
        self.assertEqual(Noticia.objects.count(), 0)

    def test_duas_execucoes_seguidas_nao_duplicam(self):
        with self.baixar_retornando(resposta(amostras.RSS), resposta(amostras.RSS)):
            coletar_noticias.apply().get()
            segunda = coletar_noticias.apply().get()
        self.assertEqual(segunda["novas"], 0)
        self.assertEqual(Noticia.objects.count(), 3)

    def test_so_fontes_ativas(self):
        FonteNoticia.objects.create(
            nome="Desligada", url_feed="https://desligada.test/rss",
            categoria_padrao=self.brasil, ativa=False)
        with self.baixar_por_url({self.fonte.url_feed: resposta(amostras.RSS)}):
            resumo = coletar_noticias.apply().get()
        self.assertEqual(resumo["fontes"], 1)

    def test_erro_em_uma_fonte_nao_para_as_outras(self):
        from apps.coleta.cliente import ErroColeta

        outra = FonteNoticia.objects.create(
            nome="Fora do ar", url_feed="https://fora.test/rss", categoria_padrao=self.brasil)
        mapa = {self.fonte.url_feed: resposta(amostras.RSS),
                outra.url_feed: ErroColeta("HTTP 503")}
        with self.baixar_por_url(mapa):
            resumo = coletar_noticias.apply().get()
        self.assertEqual((resumo["fontes"], resumo["erros"], resumo["novas"]), (2, 1, 3))
        outra.refresh_from_db()
        self.assertEqual(outra.erros_consecutivos, 1)


class ValidacaoTests(BaseColeta):
    def test_url_maior_que_o_campo_e_descartada(self):
        longa = "https://exemplo.test/" + "a" * 1100
        item = ItemFeed(titulo="Titulo valido", url=longa)
        self.assertIsNone(preparar(self.fonte, item))

    def test_item_sem_titulo_ou_link_e_descartado(self):
        self.assertIsNone(preparar(self.fonte, ItemFeed(titulo="", url="https://x.test/a")))
        self.assertIsNone(preparar(self.fonte, ItemFeed(titulo="Ok", url="javascript:alert(1)")))


class AgendamentoConfigTests(SimpleTestCase):
    def test_agenda_persistida_em_caminho_fixo(self):
        self.assertTrue(str(settings.CELERY_BEAT_SCHEDULE_FILENAME))

    def test_tarefa_agendada_expira_antes_da_proxima(self):
        opcoes = settings.CELERY_BEAT_SCHEDULE["coletar-noticias"]["options"]
        self.assertLess(opcoes["expires"], settings.COLETA_INTERVALO_MINUTOS * 60)

    def test_sinal_de_inicio_do_beat_conectado(self):
        from celery.signals import beat_init

        import config.celery as modulo

        self.assertIn(modulo.coletar_ao_iniciar_beat,
                      [ref() for _, ref in beat_init.receivers])


def servico_beat(execucoes):
    entrada = SimpleNamespace(total_run_count=execucoes)
    agenda = {agendamento.NOME_AGENDAMENTO: entrada}
    return SimpleNamespace(scheduler=SimpleNamespace(schedule=agenda))


class ColetaAoIniciarTests(BaseColeta):
    def disparar(self, servico=None):
        with mock.patch("apps.coleta.tasks.coletar_noticias.apply_async") as enfileirar:
            disparou = agendamento.disparar_se_atrasada(servico)
        return disparou, enfileirar

    def test_primeiro_start_sem_historico_coleta_na_hora(self):
        disparou, enfileirar = self.disparar(servico_beat(0))
        self.assertTrue(disparou)
        enfileirar.assert_called_once()

    def test_beat_com_agenda_salva_cuida_do_atraso_sozinho(self):
        disparou, enfileirar = self.disparar(servico_beat(5))
        self.assertFalse(disparou)
        enfileirar.assert_not_called()

    def test_coleta_recente_nao_dispara(self):
        ExecucaoColeta.objects.create(fonte=self.fonte)
        disparou, _ = self.disparar(servico_beat(0))
        self.assertFalse(disparou)

    def test_coleta_antiga_dispara(self):
        execucao = ExecucaoColeta.objects.create(fonte=self.fonte)
        ExecucaoColeta.objects.filter(pk=execucao.pk).update(
            iniciada_em=timezone.now() - timedelta(minutes=41))
        self.assertTrue(self.disparar(servico_beat(0))[0])

    def test_sem_fontes_ativas_nao_dispara(self):
        FonteNoticia.objects.update(ativa=False)
        self.assertFalse(self.disparar()[0])

    @override_settings(COLETA_EXECUTAR_AO_INICIAR=False)
    def test_pode_ser_desligado(self):
        self.assertFalse(self.disparar()[0])


class FontesBrasileirasTests(TestCase):
    def setUp(self):
        for nome in ("Brasil", "Politica", "Economia", "Mundo", "Ciencia", "Educacao"):
            Categoria.objects.create(nome=nome)

    def test_cria_fontes_ativas_e_e_idempotente(self):
        call_command("coleta_fontes", stdout=io.StringIO())
        call_command("coleta_fontes", stdout=io.StringIO())
        self.assertEqual(FonteNoticia.objects.count(), len(FONTES_BRASILEIRAS))
        self.assertFalse(FonteNoticia.objects.filter(ativa=False).exists())
        self.assertFalse(FonteNoticia.objects.filter(importar_conteudo_completo=True).exists())
        camara = FonteNoticia.objects.get(url_feed__contains="camara.leg.br")
        self.assertEqual(camara.categoria_padrao.slug, "politica")

    def test_nao_altera_fonte_existente(self):
        url = FONTES_BRASILEIRAS[0][1]
        FonteNoticia.objects.create(nome="Minha AB", url_feed=url, ativa=False,
                                    categoria_padrao=Categoria.objects.get(slug="mundo"))
        call_command("coleta_fontes", stdout=io.StringIO())
        fonte = FonteNoticia.objects.get(url_feed=url)
        self.assertFalse(fonte.ativa)
        self.assertEqual(fonte.nome, "Minha AB")

    def test_convive_com_coleta_exemplos(self):
        call_command("coleta_exemplos", stdout=io.StringIO())
        call_command("coleta_fontes", stdout=io.StringIO())
        self.assertEqual(FonteNoticia.objects.count(), len(FONTES_BRASILEIRAS))

    def test_inativas_e_listar(self):
        saida = io.StringIO()
        call_command("coleta_fontes", "--listar", stdout=saida)
        self.assertIn("BBC News Brasil", saida.getvalue())
        self.assertEqual(FonteNoticia.objects.count(), 0)
        call_command("coleta_fontes", "--inativas", stdout=io.StringIO())
        self.assertFalse(FonteNoticia.objects.filter(ativa=True).exists())

    def test_catalogo_so_tem_https_e_urls_unicas(self):
        urls = [url for _, url, _, _ in FONTES_BRASILEIRAS]
        self.assertEqual(len(urls), len(set(urls)))
        self.assertTrue(all(url.startswith("https://") for url in urls))


class FontesSemCategoriaTests(TestCase):
    def test_exige_categorias(self):
        with self.assertRaises(CommandError):
            call_command("coleta_fontes", stdout=io.StringIO())


class ApiSincronizarComTravaTests(BaseColeta):
    def test_api_responde_409_se_coleta_em_andamento(self):
        from rest_framework.test import APIClient

        admin = User.objects.create_user(
            username="chefe", email="chefe@x.test", password="SenhaForte123",
            tipo_usuario=TipoUsuario.ADMIN)
        cliente = APIClient()
        cliente.force_authenticate(admin)
        with OcupanteDaTrava():
            resposta_api = cliente.post(f"/api/coleta/fontes/{self.fonte.pk}/sincronizar/")
        self.assertEqual(resposta_api.status_code, 409)


class RodarAgendadorTests(BaseColeta):
    def executar(self, rodadas, **opcoes):
        """Roda o agendador e interrompe (Ctrl+C simulado) depois de `rodadas` esperas."""
        from apps.coleta.management.commands import rodar_agendador as modulo

        esperas = []

        def dormir(comando, segundos):
            esperas.append(segundos)
            if len(esperas) >= rodadas:
                raise KeyboardInterrupt

        saida = io.StringIO()
        with mock.patch.object(modulo.Command, "dormir", dormir):
            call_command("rodar_agendador", stdout=saida, **opcoes)
        return esperas, saida.getvalue()

    def test_coleta_ao_iniciar_e_repete_no_intervalo(self):
        with self.baixar_retornando(resposta(amostras.RSS), resposta(amostras.RSS)):
            esperas, saida = self.executar(2)
        self.assertEqual(len(esperas), 2)
        self.assertTrue(all(0 < e <= 40 * 60 for e in esperas))
        self.assertEqual(Noticia.objects.count(), 3)  # 2a rodada nao duplica
        self.assertEqual(ExecucaoColeta.objects.count(), 2)
        self.assertIn("encerrado", saida)

    def test_intervalo_configuravel(self):
        with self.baixar_retornando(resposta(amostras.RSS)):
            esperas, _ = self.executar(1, intervalo=10)
        self.assertLessEqual(esperas[0], 10 * 60)
        self.assertGreater(esperas[0], 9 * 60)

    def test_erro_inesperado_nao_derruba_o_agendador(self):
        with mock.patch("apps.coleta.management.commands.rodar_agendador.sincronizar_todas",
                        side_effect=RuntimeError("boom")):
            esperas, _ = self.executar(2)
        self.assertEqual(len(esperas), 2)  # continuou para a 2a rodada

    def test_coleta_em_andamento_e_pulada_sem_erro(self):
        with OcupanteDaTrava():
            with self.baixar_retornando() as baixar:
                self.executar(1)
        baixar.assert_not_called()
