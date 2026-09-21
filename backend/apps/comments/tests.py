from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.categories.models import Categoria
from apps.news.models import Noticia, StatusNoticia
from apps.users.models import TipoUsuario, User

from .models import Comentario


class ComentarioTests(APITestCase):
    def setUp(self):
        categoria = Categoria.objects.create(nome="Brasil")
        autor = User.objects.create_user(username="autor", email="a@t.com",
                                         password="senhaforte123", nome="Autor",
                                         tipo_usuario=TipoUsuario.JORNALISTA)
        self.noticia = Noticia.objects.create(
            titulo="Materia", conteudo="<p>x</p>", categoria=categoria, autor=autor,
            status=StatusNoticia.PUBLICADA, data_publicacao=timezone.now())
        self.leitor = User.objects.create_user(username="leitor", email="l@t.com",
                                               password="senhaforte123", nome="Leitor")
        self.outro = User.objects.create_user(username="outro", email="o@t.com",
                                              password="senhaforte123", nome="Outro")

    def test_visitante_nao_comenta(self):
        resposta = self.client.post("/api/comments/",
                                    {"noticia": self.noticia.pk, "conteudo": "oi"})
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_leitor_comenta_e_curte(self):
        self.client.force_authenticate(self.leitor)
        criado = self.client.post("/api/comments/",
                                  {"noticia": self.noticia.pk, "conteudo": "otima materia"})
        self.assertEqual(criado.status_code, status.HTTP_201_CREATED)
        curtir = self.client.post(f"/api/comments/{criado.data['id']}/curtir/")
        self.assertTrue(curtir.data["curtido"])

    def test_usuario_nao_edita_comentario_alheio(self):
        comentario = Comentario.objects.create(noticia=self.noticia, autor=self.leitor,
                                               conteudo="meu comentario")
        self.client.force_authenticate(self.outro)
        resposta = self.client.patch(f"/api/comments/{comentario.pk}/",
                                     {"conteudo": "alterado"})
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)
