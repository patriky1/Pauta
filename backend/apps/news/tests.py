from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.categories.models import Categoria
from apps.users.models import TipoUsuario, User

from .models import Noticia, StatusNoticia


class NoticiaApiTests(APITestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nome="Tecnologia")
        self.jornalista = User.objects.create_user(
            username="repo", email="repo@teste.com", password="senhaforte123",
            nome="Reporter", tipo_usuario=TipoUsuario.JORNALISTA)
        self.leitor = User.objects.create_user(
            username="leitor", email="l@teste.com", password="senhaforte123", nome="Leitor")
        self.publicada = Noticia.objects.create(
            titulo="Publicada", conteudo="<p>conteudo de teste</p>",
            categoria=self.categoria, autor=self.jornalista,
            status=StatusNoticia.PUBLICADA, data_publicacao=timezone.now())
        Noticia.objects.create(
            titulo="Rascunho", conteudo="<p>rascunho</p>", categoria=self.categoria,
            autor=self.jornalista, status=StatusNoticia.RASCUNHO)

    def test_lista_publica_esconde_rascunhos(self):
        resposta = self.client.get("/api/news/")
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data["count"], 1)

    def test_slug_gerado_automaticamente(self):
        self.assertEqual(self.publicada.slug, "publicada")

    def test_detalhe_incrementa_visualizacoes(self):
        self.client.get(f"/api/news/{self.publicada.slug}/")
        self.publicada.refresh_from_db()
        self.assertEqual(self.publicada.visualizacoes, 1)

    def test_leitor_nao_cria_noticia(self):
        self.client.force_authenticate(self.leitor)
        resposta = self.client.post("/api/admin/news/", {
            "titulo": "Nao deveria", "conteudo": "x", "categoria_id": self.categoria.pk})
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_jornalista_cria_e_publica(self):
        self.client.force_authenticate(self.jornalista)
        resposta = self.client.post("/api/admin/news/", {
            "titulo": "Nova materia", "conteudo": "<p>texto</p>",
            "categoria_id": self.categoria.pk, "status": StatusNoticia.RASCUNHO,
            "tags": ["teste"]}, format="json")
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        slug = resposta.data["slug"]
        publicar = self.client.post(f"/api/admin/news/{slug}/publicar/")
        self.assertEqual(publicar.status_code, status.HTTP_200_OK)
        self.assertEqual(publicar.data["status"], StatusNoticia.PUBLICADA)

    def test_busca_retorna_resultado(self):
        resposta = self.client.get("/api/search/?q=Publicada")
        self.assertEqual(resposta.data["total"], 1)


class CategoriaApiTests(APITestCase):
    def setUp(self):
        Categoria.objects.create(nome="Economia")

    def test_lista_categorias_publica(self):
        resposta = self.client.get("/api/categories/")
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data), 1)

    def test_criar_categoria_exige_redacao(self):
        resposta = self.client.post("/api/categories/", {"nome": "Nova"})
        self.assertIn(resposta.status_code,
                      (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


class FaixaUrgenteTests(APITestCase):
    """/api/news/breaking/: marcadas como urgentes + ultimas noticias (automatico)."""

    def setUp(self):
        from datetime import timedelta

        self.timedelta = timedelta
        self.categoria = Categoria.objects.create(nome="Brasil")
        self.autor = User.objects.create_user(
            username="repo", email="repo@teste.com", password="senhaforte123", nome="Reporter")

    def criar(self, titulo, horas_atras=0, **extras):
        extras.setdefault("status", StatusNoticia.PUBLICADA)
        return Noticia.objects.create(
            titulo=titulo, conteudo="<p>x</p>", categoria=self.categoria, autor=self.autor,
            data_publicacao=timezone.now() - self.timedelta(hours=horas_atras), **extras)

    def titulos(self):
        resposta = self.client.get("/api/news/breaking/")
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        return [item["titulo"] for item in resposta.data]

    def test_ultimas_noticias_aparecem_sem_marcar_nada(self):
        self.criar("Mais antiga", 3)
        self.criar("Mais nova", 1)
        self.assertEqual(self.titulos(), ["Mais nova", "Mais antiga"])
        self.assertFalse(Noticia.objects.filter(breaking_news=True).exists())

    def test_marcadas_manualmente_vem_primeiro(self):
        self.criar("Comum recente", 0)
        self.criar("Marcada antiga", 20, breaking_news=True)
        self.assertEqual(self.titulos(), ["Marcada antiga", "Comum recente"])

    def test_noticia_velha_nao_entra_automaticamente(self):
        self.criar("Velha", 7)
        self.assertEqual(self.titulos(), [])

    def test_rascunho_e_revisao_nunca_aparecem(self):
        self.criar("Rascunho", 0, status=StatusNoticia.RASCUNHO)
        self.criar("Em revisao", 0, status=StatusNoticia.REVISAO)
        self.assertEqual(self.titulos(), [])

    def test_respeita_o_maximo(self):
        for i in range(8):
            self.criar(f"N{i}", i * 0.1)
        self.assertEqual(len(self.titulos()), 5)

    def test_sem_duplicar_noticia_marcada_e_recente(self):
        self.criar("Unica", 0, breaking_news=True)
        self.assertEqual(self.titulos(), ["Unica"])

    def test_pode_desligar_o_automatico(self):
        from django.test import override_settings

        self.criar("Recente", 0)
        self.criar("Marcada", 0, breaking_news=True)
        with override_settings(URGENTE_AUTOMATICO=False):
            self.assertEqual(self.titulos(), ["Marcada"])

    def test_janela_configuravel(self):
        from django.test import override_settings

        self.criar("De 10h atras", 10)
        with override_settings(URGENTE_JANELA_HORAS=12):
            self.assertEqual(self.titulos(), ["De 10h atras"])

    def test_noticia_importada_pela_coleta_aparece(self):
        from apps.coleta.models import FonteNoticia

        fonte = FonteNoticia.objects.create(
            nome="Fonte X", url_feed="https://x.test/rss", categoria_padrao=self.categoria)
        self.criar("Importada", 0, fonte_externa=fonte, url_original="https://x.test/a",
                   id_externo="a")
        self.assertEqual(self.titulos(), ["Importada"])
