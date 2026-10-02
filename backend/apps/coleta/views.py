from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import EhAdministrador

from .models import ExecucaoColeta, FonteNoticia, MapeamentoCategoria, RegraCategorizacao
from .serializers import (
    ExecucaoColetaSerializer,
    FonteNoticiaSerializer,
    MapeamentoCategoriaSerializer,
    RegraCategorizacaoSerializer,
)


class FonteNoticiaViewSet(viewsets.ModelViewSet):
    """Cadastro de fontes externas (somente administradores)."""

    permission_classes = [EhAdministrador]
    serializer_class = FonteNoticiaSerializer
    queryset = FonteNoticia.objects.select_related("categoria_padrao")
    filterset_fields = ("ativa", "tipo")
    search_fields = ("nome", "url_feed")
    ordering_fields = ("nome", "ultima_sincronizacao", "total_importadas")
    throttle_scope = "escrita"

    @action(detail=True, methods=["post"])
    def sincronizar(self, request, pk=None):
        """Sincroniza esta fonte agora (mesmo inativa) e devolve o log da execucao.

        Responde 409 se a coleta agendada (ou outra sincronizacao) estiver em andamento.
        """
        from .services import MOTIVO_OCUPADA, sincronizar_fonte_exclusiva

        execucao = sincronizar_fonte_exclusiva(self.get_object())
        if execucao is None:
            return Response({"detail": MOTIVO_OCUPADA}, status=status.HTTP_409_CONFLICT)
        return Response(ExecucaoColetaSerializer(execucao).data)


class ExecucaoColetaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
    permission_classes = [EhAdministrador]
    serializer_class = ExecucaoColetaSerializer
    queryset = ExecucaoColeta.objects.select_related("fonte")
    filterset_fields = ("fonte", "status")
    ordering = ("-iniciada_em",)


class MapeamentoCategoriaViewSet(viewsets.ModelViewSet):
    permission_classes = [EhAdministrador]
    serializer_class = MapeamentoCategoriaSerializer
    queryset = MapeamentoCategoria.objects.all()
    filterset_fields = ("fonte", "categoria")


class RegraCategorizacaoViewSet(viewsets.ModelViewSet):
    permission_classes = [EhAdministrador]
    serializer_class = RegraCategorizacaoSerializer
    queryset = RegraCategorizacao.objects.select_related("categoria")
    filterset_fields = ("categoria", "ativa")
