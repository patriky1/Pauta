from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import TipoUsuario, User

from .models import Categoria


class CategoriaTests(APITestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nome="Economia")
        self.editor = User.objects.create_user(
            username="editor", email="e@teste.local", password="SenhaForte123",
            nome="Editor", tipo_usuario=TipoUsuario.EDITOR,
        )

    def test_listagem_publica(self):
        resposta = self.client.get("/api/categories/")
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data), 1)

    def test_visitante_nao_cria_categoria(self):
        resposta = self.client.post("/api/categories/", {"nome": "Nova"}, format="json")
        self.assertIn(resposta.status_code, (401, 403))

    def test_editor_cria_categoria_com_slug(self):
        self.client.force_authenticate(self.editor)
        resposta = self.client.post("/api/categories/", {"nome": "Meio Ambiente"},
                                    format="json")
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resposta.data["slug"], "meio-ambiente")
