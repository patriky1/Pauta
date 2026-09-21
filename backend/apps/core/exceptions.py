"""Padroniza o corpo de erro devolvido pela API."""
from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

MENSAGENS = {
    400: "Dados invalidos. Revise os campos e tente novamente.",
    401: "Sessao expirada. Entre novamente para continuar.",
    403: "Voce nao tem permissao para esta acao.",
    404: "Nao encontramos o que voce procurava.",
    409: "Este registro entra em conflito com um existente.",
    429: "Muitas requisicoes em pouco tempo. Aguarde um instante.",
    500: "Erro interno. Ja estamos verificando.",
}


def tratar_excecao(exc, context):
    resposta = exception_handler(exc, context)

    if resposta is None:
        if isinstance(exc, Http404):
            codigo = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, PermissionDenied):
            codigo = status.HTTP_403_FORBIDDEN
        else:
            return None
        return Response({"detail": MENSAGENS[codigo], "status": codigo}, status=codigo)

    codigo = resposta.status_code
    corpo = {"status": codigo, "detail": MENSAGENS.get(codigo, "Nao foi possivel concluir.")}

    dados = resposta.data
    if isinstance(dados, dict):
        if "detail" in dados:
            corpo["detail"] = str(dados["detail"])
        campos = {k: v for k, v in dados.items() if k != "detail"}
        if campos:
            corpo["errors"] = campos
    elif isinstance(dados, list):
        corpo["errors"] = {"non_field_errors": dados}

    resposta.data = corpo
    return resposta
