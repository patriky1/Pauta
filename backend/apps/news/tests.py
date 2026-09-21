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
