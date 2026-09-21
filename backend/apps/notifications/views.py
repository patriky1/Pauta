from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notificacao
from .serializers import NotificacaoSerializer


class NotificacaoViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    serializer_class = NotificacaoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        consulta = Notificacao.objects.filter(usuario=self.request.user)
        if self.request.query_params.get("nao_lidas") == "1":
            consulta = consulta.filter(lida=False)
        return consulta

    def list(self, request, *args, **kwargs):
        resposta = super().list(request, *args, **kwargs)
        resposta.data["nao_lidas"] = Notificacao.objects.filter(
            usuario=request.user, lida=False
        ).count()
        return resposta

    @action(detail=True, methods=["post"], url_path="lida")
    def marcar_lida(self, request, pk=None):
        notificacao = self.get_object()
        notificacao.lida = True
        notificacao.save(update_fields=["lida"])
        return Response({"lida": True})

    @action(detail=False, methods=["post"], url_path="ler-todas")
    def marcar_todas(self, request):
        total = Notificacao.objects.filter(usuario=request.user, lida=False).update(lida=True)
        return Response({"atualizadas": total})

    @action(detail=False, methods=["get"], url_path="contador")
    def contador(self, request):
        return Response(
            {"nao_lidas": Notificacao.objects.filter(
                usuario=request.user, lida=False).count()}
        )
