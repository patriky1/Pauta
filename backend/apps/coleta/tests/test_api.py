from datetime import datetime, timezone as tz

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

from apps.coleta.models import FonteNoticia
from apps.coleta.services import sincronizar_fonte
from apps.news.models import Noticia, StatusNoticia
from apps.users.models import TipoUsuario, User

from . import amostras
from .base import BaseColeta, resposta


class ApiNoticiasTests(BaseColeta):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.jornalista = User.objects.create_user(
            username="repo", email="repo@teste.com", password="senhaforte123",
            nome="Reporter", tipo_usuario=TipoUsuario.JORNALISTA)
        with self.baixar_retornando(resposta(amostras.RSS)):
            sincronizar_fonte(self.fonte)
        self.editorial = Noticia.objects.create(
            titulo="Materia da redacao", conteudo="<p>texto</p>", categoria=self.economia,
            autor=self.jornalista, status=StatusNoticia.PUBLICADA,
            data_publicacao=datetime(2026, 9, 1, 12, 0, tzinfo=tz.utc),
            imagem_url="https://img.test/redacao.jpg")

    def test_lista_traz_origem_da_fonte(self):
        dados = self.client.get("/api/news/?origem=importada").data
        self.assertEqual(dados["count"], 3)
        origem = dados["results"][0]["origem"]
        self.assertEqual(origem["fonte"], "Agencia Exemplo")
        self.assertTrue(origem["url"].startswith("https://exemplo.test/"))

    def test_materia_da_redacao_sem_origem(self):
        dados = self.client.get("/api/news/?origem=redacao").data
        self.assertEqual(dados["count"], 1)
        self.assertIsNone(dados["results"][0]["origem"])

    def test_filtro_por_fonte_e_categoria(self):
        self.assertEqual(self.client.get(f"/api/news/?fonte={self.fonte.slug}").data["count"], 3)
        self.assertEqual(self.client.get("/api/news/?categoria=politica").data["count"], 1)

    def test_ordenacao_e_paginacao(self):
        dados = self.client.get("/api/news/?ordering=-data_publicacao&page_size=2").data
        self.assertEqual(dados["count"], 4)
        self.assertEqual(len(dados["results"]), 2)
        self.assertEqual(dados["pages"], 2)
        datas = [n["data_publicacao"] for n in dados["results"]]
        self.assertEqual(datas, sorted(datas, reverse=True))
        crescente = self.client.get("/api/news/?ordering=data_publicacao").data["results"]
        self.assertEqual(crescente[0]["titulo"], "Materia da redacao")

    def test_detalhe_da_importada(self):
        noticia = Noticia.objects.get(id_externo="exemplo-10")
        dados = self.client.get(f"/api/news/{noticia.slug}/").data
        self.assertEqual(dados["origem"]["autor"], "Maria Souza")

    def test_categorias_e_destaques_continuam_funcionando(self):
        self.assertEqual(self.client.get("/api/categories/").status_code, status.HTTP_200_OK)
        destaques = self.client.get("/api/news/destaques/").data
        self.assertIsNotNone(destaques["principal"])

    def test_carrossel_prioriza_destaque_e_exige_imagem(self):
        Noticia.objects.filter(id_externo="exemplo-10").update(destaque=True)
        cache.clear()
        dados = self.client.get("/api/news/carrossel/").data
        ids = [n["id"] for n in dados["results"]]
        destaque = Noticia.objects.get(id_externo="exemplo-10")
        self.assertEqual(ids[0], destaque.pk)
        # a nota sem imagem nao entra
        sem_imagem = Noticia.objects.get(url_original="https://exemplo.test/geral/clima")
        self.assertNotIn(sem_imagem.pk, ids)
        self.assertEqual(dados["count"], len(ids))
        for campo in ("titulo", "resumo", "imagem", "categoria", "slug"):
            self.assertIn(campo, dados["results"][0])

    def test_carrossel_limite(self):
        self.assertEqual(self.client.get("/api/news/carrossel/?limite=1").data["count"], 1)
        self.assertLessEqual(self.client.get("/api/news/carrossel/?limite=999").data["count"], 10)
        self.assertEqual(self.client.get("/api/news/carrossel/?limite=abc").status_code, 200)

    def test_carrossel_atualiza_apos_nova_importacao(self):
        antes = self.client.get("/api/news/carrossel/").data["count"]
        with self.baixar_retornando(resposta(amostras.ATOM)):
            sincronizar_fonte(self.fonte)
        depois = self.client.get("/api/news/carrossel/").data["count"]
        self.assertEqual(depois, antes + 1)

    def test_carrossel_nao_mostra_rascunho(self):
        Noticia.objects.filter(fonte_externa=self.fonte).update(status=StatusNoticia.RASCUNHO)
        cache.clear()
        ids = [n["id"] for n in self.client.get("/api/news/carrossel/").data["results"]]
        self.assertEqual(ids, [self.editorial.pk])


class ApiFontesTests(BaseColeta):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="chefe", email="chefe@teste.com", password="senhaforte123",
            nome="Chefe", tipo_usuario=TipoUsuario.ADMIN)
        self.leitor = User.objects.create_user(
            username="leitor", email="l@teste.com", password="senhaforte123", nome="Leitor")

    def test_somente_admin(self):
        self.assertIn(self.client.get("/api/coleta/fontes/").status_code,
                      (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
        self.client.force_authenticate(self.leitor)
        self.assertEqual(self.client.get("/api/coleta/fontes/").status_code,
                         status.HTTP_403_FORBIDDEN)

    def test_admin_cadastra_fonte(self):
        self.client.force_authenticate(self.admin)
        resposta_api = self.client.post("/api/coleta/fontes/", {
            "nome": "Nova Fonte", "url_feed": "https://nova.test/feed.xml",
            "categoria_padrao_id": self.brasil.pk,
        }, format="json")
        self.assertEqual(resposta_api.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resposta_api.data["slug"], "nova-fonte")
        self.assertTrue(FonteNoticia.objects.filter(nome="Nova Fonte").exists())

    def test_recusa_chave_no_lugar_do_nome_da_variavel(self):
        self.client.force_authenticate(self.admin)
        resposta_api = self.client.post("/api/coleta/fontes/", {
            "nome": "Com chave", "url_feed": "https://chave.test/api",
            "categoria_padrao_id": self.brasil.pk, "chave_api_variavel": "abc123segredo",
        }, format="json")
        self.assertEqual(resposta_api.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_json_exige_mapeamento(self):
        self.client.force_authenticate(self.admin)
        resposta_api = self.client.post("/api/coleta/fontes/", {
            "nome": "API", "url_feed": "https://api.test/v1", "tipo": "API_JSON",
            "categoria_padrao_id": self.brasil.pk, "mapeamento_json": {"itens": "x"},
        }, format="json")
        self.assertEqual(resposta_api.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sincronizar_pela_api_e_ver_log(self):
        self.client.force_authenticate(self.admin)
        with self.baixar_retornando(resposta(amostras.RSS)):
            resposta_api = self.client.post(f"/api/coleta/fontes/{self.fonte.pk}/sincronizar/")
        self.assertEqual(resposta_api.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta_api.data["novas"], 3)
        log = self.client.get(f"/api/coleta/execucoes/?fonte={self.fonte.pk}").data
        self.assertEqual(log["count"], 1)
