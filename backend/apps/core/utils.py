"""Funcoes utilitarias compartilhadas."""
import re
from html import unescape

from django.utils.text import slugify

PALAVRAS_POR_MINUTO = 200


def slug_unico(modelo, texto, instancia=None, campo="slug"):
    """Gera um slug unico para o model informado."""
    base = slugify(texto)[:180] or "item"
    slug = base
    contador = 2
    consulta = modelo.objects.all()
    if instancia is not None and instancia.pk:
        consulta = consulta.exclude(pk=instancia.pk)
    while consulta.filter(**{campo: slug}).exists():
        slug = f"{base}-{contador}"
        contador += 1
    return slug


def texto_puro(html):
    """Remove tags HTML preservando o texto."""
    return unescape(re.sub(r"<[^>]+>", " ", html or "")).strip()


def calcular_tempo_leitura(conteudo):
    """Tempo estimado de leitura, em minutos (minimo 1)."""
    palavras = len(texto_puro(conteudo).split())
    return max(1, round(palavras / PALAVRAS_POR_MINUTO))


def ip_do_request(request):
    encaminhado = request.META.get("HTTP_X_FORWARDED_FOR")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def chave_sessao(request):
    """Identificador estavel para visitantes nao autenticados."""
    if request.user.is_authenticated:
        return f"user-{request.user.pk}"
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key or ip_do_request(request)
