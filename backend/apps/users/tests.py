from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import TipoUsuario, User


class AutenticacaoTests(APITestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="maria", email="maria@teste.com", password="senhaforte123", nome="Maria"
        )

    def test_cadastro_cria_usuario_e_retorna_tokens(self):
        resposta = self.client.post(reverse("auth-registro"), {
            "nome": "Joao", "username": "joao", "email": "joao@teste.com",
            "password": "senhaforte123", "password_confirm": "senhaforte123",
        })
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", resposta.data)
        self.assertTrue(User.objects.filter(username="joao").exists())

    def test_cadastro_rejeita_senhas_diferentes(self):
        resposta = self.client.post(reverse("auth-registro"), {
            "nome": "Joao", "username": "joao2", "email": "joao2@teste.com",
            "password": "senhaforte123", "password_confirm": "outrasenha123",
        })
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_aceita_email(self):
        resposta = self.client.post(reverse("auth-login"),
                                    {"username": "maria@teste.com",
                                     "password": "senhaforte123"})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data["user"]["username"], "maria")

    def test_perfil_exige_autenticacao(self):
        self.assertEqual(self.client.get(reverse("auth-perfil")).status_code,
                         status.HTTP_401_UNAUTHORIZED)

    def test_perfil_autenticado(self):
        self.client.force_authenticate(self.usuario)
        resposta = self.client.get(reverse("auth-perfil"))
        self.assertEqual(resposta.data["email"], "maria@teste.com")


class PermissaoAdminTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="chefe", email="chefe@teste.com", password="senhaforte123",
            nome="Chefe", tipo_usuario=TipoUsuario.ADMIN)
        self.leitor = User.objects.create_user(
            username="leitor", email="leitor@teste.com", password="senhaforte123",
            nome="Leitor")

    def test_leitor_nao_lista_usuarios(self):
        self.client.force_authenticate(self.leitor)
        resposta = self.client.get("/api/admin/users/")
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_bloqueia_usuario(self):
        self.client.force_authenticate(self.admin)
        resposta = self.client.post(f"/api/admin/users/{self.leitor.pk}/bloquear/",
                                    {"motivo": "spam"})
        self.leitor.refresh_from_db()
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertFalse(self.leitor.is_active)
