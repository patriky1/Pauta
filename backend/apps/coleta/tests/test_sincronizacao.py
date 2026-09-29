from datetime import timedelta
from io import StringIO
from unittest import mock

from django.core.cache import cache
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone

from apps.coleta.cliente import ErroColeta
from apps.coleta.models import (
    ExecucaoColeta,
    FonteNoticia,
    MapeamentoCategoria,
    RegraCategorizacao,
)
from apps.coleta.services import CHAVE_TRAVA, sincronizar_fonte, sincronizar_todas
from apps.news.models import Noticia, StatusNoticia
from apps.users.models import TipoUsuario, User

from . import amostras
from .base import BaseColeta, resposta


class ColetaTests(BaseColeta):
    def test_importa_campos_obrigatorios(self):
        with self.baixar_retornando(resposta(amostras.RSS)):
            execucao = sincronizar_fonte(self.fonte)

        self.assertEqual(execucao.status, ExecucaoColeta.Status.SUCESSO)
        self.assertEqual(execucao.novas, 3)
        noticia = Noticia.objects.get(id_externo="exemplo-10")
        self.assertEqual(noticia.titulo, "Senado aprova reforma tributaria em segundo turno")
        self.assertEqual(noticia.url_original, "https://exemplo.test/politica/reforma?id=10")
        self.assertEqual(noticia.fonte_externa, self.fonte)
        self.assertEqual(noticia.autor_original, "Maria Souza")
        self.assertEqual(noticia.imagem_url, "https://img.test/g.jpg")
        self.assertEqual(noticia.imagem_credito, "Imagem: Agencia Exemplo")
        self.assertEqual(noticia.status, StatusNoticia.PUBLICADA)
        self.assertTrue(noticia.slug)
        self.assertTrue(noticia.hash_conteudo)
        self.assertEqual(noticia.data_publicacao.isoformat(), "2026-09-29T13:00:00+00:00")
        self.assertIn("Texto aprovado", noticia.resumo)
        # por padrao so o resumo e importado, sem script
        self.assertNotIn("Paragrafo completo", noticia.conteudo)
        self.assertNotIn("script", noticia.conteudo)
        # a conta tecnica assina, mas nao e da redacao nem faz login
        self.assertEqual(noticia.autor.tipo_usuario, TipoUsuario.USUARIO)
        self.assertFalse(noticia.autor.has_usable_password())
        self.assertNotIn(noticia.autor, User.objects.redacao())

    def test_conteudo_completo_so_quando_permitido_e_sanitizado(self):
        self.fonte.importar_conteudo_completo = True
        self.fonte.save()
        with self.baixar_retornando(resposta(amostras.RSS)):
            sincronizar_fonte(self.fonte)
        noticia = Noticia.objects.get(id_externo="exemplo-10")
        self.assertIn("Paragrafo completo", noticia.conteudo)
        self.assertNotIn("javascript", noticia.conteudo)
        self.assertNotIn("onclick", noticia.conteudo)
        self.assertNotIn("<img", noticia.conteudo)
        self.assertIn('href="https://fonte.test/doc"', noticia.conteudo)

    def test_fonte_em_revisao(self):
        self.fonte.publicar_automaticamente = False
        self.fonte.save()
        with self.baixar_retornando(resposta(amostras.RSS)):
            sincronizar_fonte(self.fonte)
        self.assertFalse(Noticia.objects.publicadas().exists())
        self.assertEqual(Noticia.objects.filter(status=StatusNoticia.REVISAO).count(), 3)

    def test_atualiza_estado_da_fonte(self):
        with self.baixar_retornando(resposta(amostras.RSS, etag='"v1"')):
            sincronizar_fonte(self.fonte)
        self.fonte.refresh_from_db()
        self.assertEqual(self.fonte.total_importadas, 3)
        self.assertEqual(self.fonte.etag, '"v1"')
        self.assertIsNotNone(self.fonte.ultimo_sucesso)
        self.assertEqual(self.fonte.erros_consecutivos, 0)

    def test_304_nao_altera_nada(self):
        with self.baixar_retornando(resposta(nao_modificado=True)):
            execucao = sincronizar_fonte(self.fonte)
        self.assertEqual(execucao.status, ExecucaoColeta.Status.SUCESSO)
        self.assertIn("304", execucao.mensagem)
        self.assertEqual(Noticia.objects.count(), 0)

    @override_settings(COLETA_IDADE_MAXIMA_DIAS=1)
    def test_ignora_noticias_antigas(self):
        antigo = amostras.RSS.replace(b"Tue, 29 Sep 2026", b"Tue, 01 Jan 2019")
        with self.baixar_retornando(resposta(antigo)):
            execucao = sincronizar_fonte(self.fonte)
        # os 2 itens com data de 2019 ficam de fora; o item sem data entra com a data de agora
        self.assertEqual(execucao.novas, 1)
        self.assertEqual(execucao.ignoradas, 2)

    def test_data_futura_vira_agora(self):
        futuro = amostras.RSS.replace(b"Tue, 29 Sep 2026", b"Fri, 29 Sep 2034")
        with self.baixar_retornando(resposta(futuro)):
            sincronizar_fonte(self.fonte)
        self.assertFalse(Noticia.objects.filter(data_publicacao__gt=timezone.now()).exists())


class DuplicidadeTests(BaseColeta):
    def test_sincronizacao_idempotente(self):
        with self.baixar_retornando(resposta(amostras.RSS), resposta(amostras.RSS)):
            primeira = sincronizar_fonte(self.fonte)
            antes = {n.pk: (n.titulo, n.atualizado_em) for n in Noticia.objects.all()}
            segunda = sincronizar_fonte(self.fonte)
        depois = {n.pk: (n.titulo, n.atualizado_em) for n in Noticia.objects.all()}
        self.assertEqual(primeira.novas, 3)
        self.assertEqual(segunda.novas, 0)
        self.assertEqual(segunda.atualizadas, 0)
        self.assertEqual(segunda.ignoradas, 3)
        self.assertEqual(antes, depois)

    def test_mesma_url_com_guid_diferente(self):
        outro_guid = amostras.RSS.replace(b"exemplo-10", b"exemplo-10-v2")
        with self.baixar_retornando(resposta(amostras.RSS), resposta(outro_guid)):
            sincronizar_fonte(self.fonte)
            segunda = sincronizar_fonte(self.fonte)
        self.assertEqual(segunda.novas, 0)
        self.assertEqual(Noticia.objects.count(), 3)

    def test_url_com_rastreio_diferente_e_a_mesma(self):
        rastreio = amostras.RSS.replace(b"utm_source=rss", b"utm_source=twitter&amp;utm_medium=x")
        rastreio = rastreio.replace(b"exemplo-10", b"exemplo-10-b")
        with self.baixar_retornando(resposta(amostras.RSS), resposta(rastreio)):
            sincronizar_fonte(self.fonte)
            sincronizar_fonte(self.fonte)
        self.assertEqual(Noticia.objects.count(), 3)

    def test_mesmo_titulo_url_nova_e_barrado_pelo_hash(self):
        url_nova = amostras.RSS.replace(b"/politica/reforma?", b"/politica/reforma-2?")
        url_nova = url_nova.replace(b"exemplo-10", b"exemplo-99")
        with self.baixar_retornando(resposta(amostras.RSS), resposta(url_nova)):
            sincronizar_fonte(self.fonte)
            sincronizar_fonte(self.fonte)
        self.assertEqual(Noticia.objects.count(), 3)

    def test_mesma_materia_em_duas_fontes_entra_uma_vez(self):
        outra = FonteNoticia.objects.create(
            nome="Espelho", url_feed="https://espelho.test/rss", categoria_padrao=self.brasil)
        with self.baixar_retornando(resposta(amostras.RSS), resposta(amostras.RSS)):
            sincronizar_fonte(self.fonte)
            execucao = sincronizar_fonte(outra)
        self.assertEqual(execucao.novas, 0)
        self.assertEqual(Noticia.objects.count(), 3)

    def test_item_repetido_no_mesmo_feed(self):
        inicio = amostras.RSS.index(b"<item>")
        fim = amostras.RSS.index(b"</item>") + len(b"</item>")
        duplicado = amostras.RSS.replace(b"</channel>", amostras.RSS[inicio:fim] + b"</channel>")
        with self.baixar_retornando(resposta(duplicado)):
            execucao = sincronizar_fonte(self.fonte)
        self.assertEqual(execucao.novas, 3)
        self.assertEqual(Noticia.objects.count(), 3)

    def test_atualiza_quando_a_fonte_informa_mudanca(self):
        with self.baixar_retornando(resposta(amostras.ATOM)):
            sincronizar_fonte(self.fonte)
        noticia = Noticia.objects.get()
        # simula que a importacao aconteceu antes da data <updated> do feed
        Noticia.objects.filter(pk=noticia.pk).update(
            atualizado_em=noticia.data_publicacao - timedelta(hours=1))
        novo = amostras.ATOM.replace(b"chega ao SUS", b"chega ao SUS em outubro")
        novo = novo.replace(b"2026-09-28T09:15:00-03:00", b"2026-09-28T18:00:00-03:00")
        with self.baixar_retornando(resposta(novo)):
            execucao = sincronizar_fonte(self.fonte)
        noticia.refresh_from_db()
        self.assertEqual(execucao.atualizadas, 1)
        self.assertEqual(noticia.titulo, "Nova vacina contra dengue chega ao SUS em outubro")
        self.assertEqual(Noticia.objects.count(), 1)

    def test_nao_desfaz_edicao_da_redacao(self):
        with self.baixar_retornando(resposta(amostras.ATOM)):
            sincronizar_fonte(self.fonte)
        noticia = Noticia.objects.get()
        noticia.titulo = "Titulo corrigido pela redacao"
        noticia.save()
        with self.baixar_retornando(resposta(amostras.ATOM)):
            sincronizar_fonte(self.fonte)
        noticia.refresh_from_db()
        self.assertEqual(noticia.titulo, "Titulo corrigido pela redacao")


class CategorizacaoTests(BaseColeta):
    def _categoria_de(self, id_ou_url):
        return Noticia.objects.get(url_original=id_ou_url).categoria

    def test_nome_da_categoria_no_feed(self):
        with self.baixar_retornando(resposta(amostras.RSS)):
            sincronizar_fonte(self.fonte)
        self.assertEqual(self._categoria_de("https://exemplo.test/politica/reforma?id=10"),
                         self.politica)

    def test_mapeamento_da_fonte(self):
        MapeamentoCategoria.objects.create(fonte=self.fonte, termo_origem="futebol",
                                           categoria=self.esportes)
        with self.baixar_retornando(resposta(amostras.RSS)):
            sincronizar_fonte(self.fonte)
        self.assertEqual(self._categoria_de("https://exemplo.test/esportes/amistoso"),
                         self.esportes)

    def test_palavras_chave(self):
        RegraCategorizacao.objects.create(categoria=self.esportes, palavras_chave="selecao, gol")
        with self.baixar_retornando(resposta(amostras.RSS)):
            sincronizar_fonte(self.fonte)
        self.assertEqual(self._categoria_de("https://exemplo.test/esportes/amistoso"),
                         self.esportes)

    def test_categoria_padrao(self):
        with self.baixar_retornando(resposta(amostras.RSS)):
            sincronizar_fonte(self.fonte)
        self.assertEqual(self._categoria_de("https://exemplo.test/geral/clima"), self.brasil)


class FalhaDeFonteTests(BaseColeta):
    def test_erro_de_rede_fica_registrado(self):
        with self.baixar_retornando(ErroColeta("A fonte respondeu HTTP 503.")):
            execucao = sincronizar_fonte(self.fonte)
        self.fonte.refresh_from_db()
        self.assertEqual(execucao.status, ExecucaoColeta.Status.ERRO)
        self.assertIn("503", execucao.mensagem)
        self.assertEqual(self.fonte.erros_consecutivos, 1)
        self.assertIn("503", self.fonte.ultimo_erro)
        self.assertIsNotNone(self.fonte.ultima_sincronizacao)
        self.assertIsNone(self.fonte.ultimo_sucesso)

    def test_feed_invalido(self):
        with self.baixar_retornando(resposta(b"<html>pagina de erro</html>")):
            execucao = sincronizar_fonte(self.fonte)
        self.assertEqual(execucao.status, ExecucaoColeta.Status.ERRO)

    def test_erro_inesperado_nao_propaga(self):
        with self.baixar_retornando(RuntimeError("bug qualquer")):
            execucao = sincronizar_fonte(self.fonte)
        self.assertEqual(execucao.status, ExecucaoColeta.Status.ERRO)

    def test_uma_fonte_falha_e_as_outras_continuam(self):
        quebradas = [
            FonteNoticia.objects.create(nome=f"Quebrada {i}", url_feed=f"https://q{i}.test/rss",
                                        categoria_padrao=self.brasil)
            for i in range(2)
        ]
        # uma fonte boa entre duas quebradas: qualquer que seja a ordem, a boa e processada
        with self.baixar_por_url({
            self.fonte.url_feed: resposta(amostras.RSS),
            quebradas[0].url_feed: ErroColeta("Tempo esgotado"),
            quebradas[1].url_feed: RuntimeError("erro inesperado"),
        }):
            resumo = sincronizar_todas()
        self.assertEqual(resumo["fontes"], 3)
        self.assertEqual(resumo["erros"], 2)
        self.assertEqual(resumo["novas"], 3)
        for fonte in quebradas:
            fonte.refresh_from_db()
            self.assertEqual(fonte.erros_consecutivos, 1)

    def test_item_com_erro_nao_derruba_os_demais(self):
        original = Noticia.save
        chamadas = {"n": 0}

        def falhar_no_primeiro(noticia, *args, **kwargs):
            chamadas["n"] += 1
            if chamadas["n"] == 1:
                raise ValueError("falha simulada")
            return original(noticia, *args, **kwargs)

        with self.baixar_retornando(resposta(amostras.RSS)), \
                mock.patch.object(Noticia, "save", falhar_no_primeiro):
            execucao = sincronizar_fonte(self.fonte)
        self.assertEqual(execucao.status, ExecucaoColeta.Status.PARCIAL)
        self.assertEqual(execucao.novas, 2)
        self.assertIn("falha simulada", execucao.mensagem)

    def test_fontes_inativas_sao_puladas(self):
        self.fonte.ativa = False
        self.fonte.save()
        with self.baixar_retornando() as baixar:
            resumo = sincronizar_todas()
        self.assertEqual(resumo["fontes"], 0)
        baixar.assert_not_called()

    def test_trava_impede_coleta_simultanea(self):
        cache.add(CHAVE_TRAVA, "ocupado", 60)
        resumo = sincronizar_todas()
        self.assertFalse(resumo["executada"])
        cache.delete(CHAVE_TRAVA)

    def test_trava_e_liberada_apos_a_coleta(self):
        with self.baixar_retornando(resposta(amostras.RSS)):
            sincronizar_todas()
        self.assertIsNone(cache.get(CHAVE_TRAVA))

    @override_settings(COLETA_RETENCAO_LOGS_DIAS=30)
    def test_logs_antigos_sao_apagados(self):
        antiga = ExecucaoColeta.objects.create(fonte=self.fonte)
        ExecucaoColeta.objects.filter(pk=antiga.pk).update(
            iniciada_em=timezone.now() - timedelta(days=31))
        with self.baixar_retornando(resposta(amostras.RSS)):
            sincronizar_todas()
        self.assertFalse(ExecucaoColeta.objects.filter(pk=antiga.pk).exists())


class ApiJsonTests(BaseColeta):
    def test_api_com_chave_do_ambiente(self):
        self.fonte.tipo = FonteNoticia.Tipo.API_JSON
        self.fonte.mapeamento_json = amostras.MAPEAMENTO_API
        self.fonte.chave_api_variavel = "PAUTA_TESTE_CHAVE"
        self.fonte.chave_api_parametro = "header:X-Api-Key"
        self.fonte.save()
        import json

        with mock.patch.dict("os.environ", {"PAUTA_TESTE_CHAVE": "segredo"}), \
                self.baixar_retornando(resposta(json.dumps(amostras.API_JSON).encode())) as baixar:
            execucao = sincronizar_fonte(self.fonte)
        self.assertEqual(execucao.novas, 1)
        self.assertEqual(baixar.call_args.kwargs["cabecalhos"], {"X-Api-Key": "segredo"})
        self.assertEqual(Noticia.objects.get().categoria, self.economia)

    def test_variavel_ausente_vira_erro_claro(self):
        self.fonte.chave_api_variavel = "PAUTA_VARIAVEL_QUE_NAO_EXISTE"
        self.fonte.save()
        with self.baixar_retornando() as baixar:
            execucao = sincronizar_fonte(self.fonte)
        baixar.assert_not_called()
        self.assertIn("PAUTA_VARIAVEL_QUE_NAO_EXISTE", execucao.mensagem)


class ImagemColetaTests(BaseColeta):
    LOGO = "https://cdn.test/assets/logo-agenciabrasil.svg"

    def importar(self):
        with self.baixar_retornando(resposta(amostras.RSS_LOGO_NO_TEXTO)):
            sincronizar_fonte(self.fonte)

    def test_foto_vem_da_tag_de_destaque_e_nunca_do_logo(self):
        self.importar()
        com_tag = Noticia.objects.get(id_externo="1703522 at abr.test")
        self.assertIn("dolar.jpg", com_tag.imagem_url)
        self.assertEqual(com_tag.imagem_credito, "Imagem: Agencia Exemplo")
        preguicosa = Noticia.objects.get(id_externo="lazy-1")
        self.assertIn("foto.jpg", preguicosa.imagem_url)
        # so tinha o logo: fica sem imagem em vez de usar o logo como foto
        sem_foto = Noticia.objects.get(id_externo="sem-foto-1")
        self.assertEqual(sem_foto.imagem_url, "")
        self.assertEqual(sem_foto.imagem_credito, "")

    def test_comando_troca_logo_ja_salvo_pela_foto_real(self):
        self.importar()
        noticia = Noticia.objects.get(id_externo="1703522 at abr.test")
        noticia.imagem_url = self.LOGO
        noticia.save(update_fields=["imagem_url"])
        # uma noticia que nao esta mais no feed e ficou com o logo
        antiga = Noticia.objects.get(id_externo="sem-foto-1")
        antiga.imagem_url = self.LOGO
        antiga.imagem_credito = "Imagem: Agencia Exemplo"
        antiga.save(update_fields=["imagem_url", "imagem_credito"])
        # uma com foto de verdade nao pode ser tocada
        boa = Noticia.objects.get(id_externo="lazy-1")
        foto_boa = boa.imagem_url

        saida = StringIO()
        with self.baixar_retornando(resposta(amostras.RSS_LOGO_NO_TEXTO)):
            call_command("coleta_reparar_imagens", stdout=saida)

        noticia.refresh_from_db()
        antiga.refresh_from_db()
        boa.refresh_from_db()
        self.assertIn("dolar.jpg", noticia.imagem_url)
        self.assertEqual(antiga.imagem_url, "")  # so tinha o logo no feed tambem
        self.assertEqual(boa.imagem_url, foto_boa)
        self.assertIn("recuperada", saida.getvalue())
