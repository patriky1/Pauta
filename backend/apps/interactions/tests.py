from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.categories.models import Categoria
from apps.news.models import Noticia, StatusNoticia
from apps.users.models import TipoUsuario, User


class FavoritoHistoricoTests(APITestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nome="Saude")
        autor = User.objects.create_user(username="autor", email="a@t.com",
                                         password="senhaforte123", nome="Autor",
                                         tipo_usuario=TipoUsuario.AUTOR)
        self.noticia = Noticia.objects.create(
            titulo="Materia", conteudo="<p>x</p>", categoria=self.categoria, autor=autor,
            status=StatusNoticia.PUBLICADA, data_publicacao=timezone.now())
        self.leitor = User.objects.create_user(username="leitor", email="l@t.com",
                                               password="senhaforte123", nome="Leitor")

    def test_favoritar_e_desfavoritar(self):
        self.client.force_authenticate(self.leitor)
        primeiro = self.client.post("/api/favorites/", {"noticia": self.noticia.pk})
        self.assertTrue(primeiro.data["favoritada"])
        segundo = self.client.post("/api/favorites/", {"noticia": self.noticia.pk})
        self.assertFalse(segundo.data["favoritada"])

    def test_historico_registrado_na_leitura(self):
        self.client.force_authenticate(self.leitor)
        self.client.get(f"/api/news/{self.noticia.slug}/")
        historico = self.client.get("/api/history/")
        self.assertEqual(historico.data["count"], 1)

    def test_seguir_categoria(self):
        self.client.force_authenticate(self.leitor)
        resposta = self.client.post("/api/follow/categories/",
                                    {"valor": self.categoria.slug})
        self.assertTrue(resposta.data["seguindo"])

    def test_favoritos_exigem_login(self):
        self.assertEqual(self.client.get("/api/favorites/").status_code,
                         status.HTTP_401_UNAUTHORIZED)
