from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.core.permissions import EhAdministrador, EhDonoOuSomenteLeitura

from .models import Comentario, CurtidaComentario, Denuncia
from .serializers import ComentarioSerializer, DenunciaSerializer


class ComentarioViewSet(viewsets.ModelViewSet):
    serializer_class = ComentarioSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, EhDonoOuSomenteLeitura]
    throttle_scope = "escrita"
    ordering = ("-criado_em",)

    def get_queryset(self):
        consulta = (
            Comentario.objects.select_related("autor", "noticia")
            .annotate(total_curtidas=Count("curtidas", distinct=True))
        )
        usuario = self.request.user
        moderador = usuario.is_authenticated and usuario.e_editor
        if not moderador:
            consulta = consulta.filter(status=Comentario.Status.PUBLICADO)
        noticia = self.request.query_params.get("noticia")
        if noticia:
            consulta = consulta.filter(noticia_id=noticia)
        if self.action == "list" and self.request.query_params.get("todos") != "1":
            consulta = consulta.filter(resposta_a__isnull=True)
        return consulta

    def perform_create(self, serializer):
        comentario = serializer.save()
        from apps.notifications.services import notificar_resposta

        if comentario.resposta_a:
            notificar_resposta(comentario)

    def destroy(self, request, *args, **kwargs):
        comentario = self.get_object()
        comentario.status = Comentario.Status.REMOVIDO
        comentario.conteudo = "[comentario removido]"
        comentario.save(update_fields=["status", "conteudo", "atualizado_em"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def curtir(self, request, pk=None):
        comentario = self.get_object()
        curtida, criada = CurtidaComentario.objects.get_or_create(
            comentario=comentario, usuario=request.user
        )
        if not criada:
            curtida.delete()
        return Response(
            {"curtido": criada, "total_curtidas": comentario.curtidas.count()}
        )

    @action(detail=True, methods=["post"], permission_classes=[EhAdministrador])
    def ocultar(self, request, pk=None):
        comentario = self.get_object()
        comentario.status = Comentario.Status.OCULTO
        comentario.save(update_fields=["status", "atualizado_em"])
        return Response({"status": comentario.status})

    @action(detail=True, methods=["post"], permission_classes=[EhAdministrador])
    def aprovar(self, request, pk=None):
        comentario = self.get_object()
        comentario.status = Comentario.Status.PUBLICADO
        comentario.save(update_fields=["status", "atualizado_em"])
        return Response({"status": comentario.status})


class DenunciaViewSet(viewsets.ModelViewSet):
    serializer_class = DenunciaSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        return [EhAdministrador()]

    def get_queryset(self):
        consulta = Denuncia.objects.select_related("usuario", "comentario")
        situacao = self.request.query_params.get("status")
        if situacao:
            consulta = consulta.filter(status=situacao.upper())
        return consulta
