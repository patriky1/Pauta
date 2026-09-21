from rest_framework.permissions import SAFE_METHODS, BasePermission

PAPEIS_REDACAO = {"ADMIN", "EDITOR", "JORNALISTA", "AUTOR"}
PAPEIS_EDICAO = {"ADMIN", "EDITOR"}


def _papel(usuario):
    return getattr(usuario, "tipo_usuario", "")


class EhAdministrador(BasePermission):
    message = "Apenas administradores podem executar esta acao."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(
            usuario.is_authenticated and (usuario.is_superuser or _papel(usuario) == "ADMIN")
        )


class EhEquipeRedacao(BasePermission):
    """Permite leitura publica e escrita apenas para a redacao."""

    message = "Voce precisa fazer parte da redacao para publicar conteudo."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        usuario = request.user
        return bool(
            usuario.is_authenticated
            and (usuario.is_superuser or _papel(usuario) in PAPEIS_REDACAO)
        )


class EhAutorOuEditor(BasePermission):
    """Autor mexe no que e dele; editor e admin mexem em tudo."""

    message = "Voce so pode alterar conteudo de sua autoria."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        usuario = request.user
        if usuario.is_superuser or _papel(usuario) in PAPEIS_EDICAO:
            return True
        dono = getattr(obj, "autor", None) or getattr(obj, "criado_por", None)
        return dono == usuario


class EhDonoOuSomenteLeitura(BasePermission):
    message = "Voce so pode alterar os seus proprios registros."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        usuario = request.user
        if usuario.is_superuser or _papel(usuario) in PAPEIS_EDICAO:
            return True
        dono = getattr(obj, "autor", None) or getattr(obj, "usuario", None)
        return dono == usuario
