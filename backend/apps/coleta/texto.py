"""Limpeza de texto, sanitizacao de HTML e normalizacao de URLs.

Modulo sem dependencia do Django: pode ser testado isoladamente.
"""
import hashlib
import re
import unicodedata
from html import escape, unescape
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# parametros de rastreamento removidos da URL antes de comparar duplicatas
PARAMETROS_RASTREIO = {
    "fbclid", "gclid", "dclid", "msclkid", "igshid", "mc_cid", "mc_eid",
    "_ga", "yclid", "ref_src", "cmpid", "ncid",
}

TAGS_PERMITIDAS = {
    "p", "br", "strong", "b", "em", "i", "u", "ul", "ol", "li",
    "blockquote", "h2", "h3", "h4", "a",
}
TAGS_VAZIAS = {"br"}
# o conteudo destas tags e descartado inteiro (nao so a tag)
TAGS_DESCARTADAS = {"script", "style", "iframe", "object", "embed", "noscript",
                    "template", "svg", "math", "form", "button", "select", "textarea"}
TAGS_BLOCO = {"p", "div", "section", "article", "li", "br", "h1", "h2", "h3", "h4",
              "h5", "h6", "blockquote", "tr", "figcaption"}


# nomes de arquivo que indicam logo, pixel de rastreamento ou reserva de carregamento
_IMAGEM_RUIM = re.compile(
    r"(?<![a-z])(?:logo|logomarca|spacer|blank|placeholder|loading|sprite|favicon)(?![a-z])"
    r"|/ebc\.(?:png|gif)(?:\?|$)|[?&]o=rss\b|1x1",
    re.I,
)


def imagem_util(url, alt="", estilo=""):
    """False para logos, pixels de rastreamento, SVG e reservas de carregamento.

    Alguns feeds abrem cada materia com o logo do veiculo e fecham com imagens de
    1 pixel; sem este filtro o logo viraria a "foto" da noticia.
    """
    url = (url or "").strip()
    if not url or url.lower().startswith("data:"):
        return False
    caminho = url.split("?", 1)[0].lower()
    if caminho.endswith((".svg", ".ico")):
        return False
    if _IMAGEM_RUIM.search(url):
        return False
    if re.search(r"(?<![a-z])logo(?![a-z])", (alt or "").lower()):
        return False
    if re.search(r"(?:width|height)\s*:\s*1px", estilo or "", re.I):
        return False
    return True


def url_segura(url):
    """Aceita apenas http/https com host. Qualquer outra coisa vira string vazia."""
    url = (url or "").strip()
    if not url:
        return ""
    try:
        partes = urlsplit(url)
    except ValueError:
        return ""
    if partes.scheme.lower() not in {"http", "https"} or not partes.netloc:
        return ""
    return url


def normalizar_url(url):
    """Forma canonica usada para detectar duplicatas.

    Minusculas no esquema/host, sem fragmento, sem parametros de rastreio (utm_* etc.)
    e sem barra final (exceto na raiz). A ordem dos demais parametros e mantida.
    """
    url = url_segura(url)
    if not url:
        return ""
    partes = urlsplit(url)
    host = partes.netloc.lower()
    if host.endswith(":80") and partes.scheme.lower() == "http":
        host = host[:-3]
    if host.endswith(":443") and partes.scheme.lower() == "https":
        host = host[:-4]
    parametros = [
        (chave, valor)
        for chave, valor in parse_qsl(partes.query, keep_blank_values=True)
        if not chave.lower().startswith("utm_") and chave.lower() not in PARAMETROS_RASTREIO
    ]
    caminho = partes.path or "/"
    if len(caminho) > 1 and caminho.endswith("/"):
        caminho = caminho.rstrip("/") or "/"
    return urlunsplit((partes.scheme.lower(), host, caminho, urlencode(parametros), ""))


def normalizar_texto(texto):
    """Minusculas, sem acentos, sem pontuacao e com espacos simples."""
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return texto.strip()


def gerar_hash(*partes):
    base = "|".join(str(parte) for parte in partes)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


class _ExtratorTexto(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes = []
        self._descartando = 0

    def handle_starttag(self, tag, attrs):
        if tag in TAGS_DESCARTADAS:
            self._descartando += 1
        elif tag in TAGS_BLOCO:
            self.partes.append(" ")

    def handle_endtag(self, tag):
        if tag in TAGS_DESCARTADAS and self._descartando:
            self._descartando -= 1
        elif tag in TAGS_BLOCO:
            self.partes.append(" ")

    def handle_data(self, dados):
        if not self._descartando:
            self.partes.append(dados)


def texto_limpo(html):
    """Remove todo o HTML e devolve texto corrido."""
    if not html:
        return ""
    extrator = _ExtratorTexto()
    try:
        extrator.feed(str(html))
        extrator.close()
        texto = "".join(extrator.partes)
    except Exception:  # HTML muito quebrado: cai para a remocao simples
        texto = unescape(re.sub(r"<[^>]+>", " ", str(html)))
    return re.sub(r"\s+", " ", texto).strip()


def resumir(texto, limite=480):
    """Corta no limite respeitando palavras inteiras."""
    texto = (texto or "").strip()
    if len(texto) <= limite:
        return texto
    corte = texto[: limite - 1].rsplit(" ", 1)[0].rstrip(" ,;:.-")
    return f"{corte}…"


class _Sanitizador(HTMLParser):
    """Mantem apenas uma lista fechada de tags e atributos seguros."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.saida = []
        self.pilha = []
        self._descartando = 0

    def handle_starttag(self, tag, attrs):
        if tag in TAGS_DESCARTADAS:
            self._descartando += 1
            return
        if self._descartando or tag not in TAGS_PERMITIDAS:
            if tag in {"div", "section", "article"}:
                self._abrir("p")
            return
        if tag in TAGS_VAZIAS:
            self.saida.append("<br>")
            return
        if tag == "a":
            href = url_segura(dict(attrs).get("href"))
            if not href:
                # link sem destino seguro: mantem apenas o texto
                self.pilha.append("a-ignorado")
                return
            self.pilha.append("a")
            self.saida.append(
                f'<a href="{escape(href, quote=True)}" target="_blank" '
                f'rel="noopener noreferrer nofollow">'
            )
            return
        self._abrir(tag)

    def _abrir(self, tag):
        # nao aninha paragrafos: fecha o anterior
        if tag == "p" and "p" in self.pilha:
            self._fechar("p")
        self.pilha.append(tag)
        self.saida.append(f"<{tag}>")

    def _fechar(self, tag):
        if tag not in self.pilha:
            return
        while self.pilha:
            aberta = self.pilha.pop()
            if aberta != "a-ignorado":
                self.saida.append(f"</{aberta}>")
            if aberta == tag:
                break

    def handle_startendtag(self, tag, attrs):
        if tag in TAGS_VAZIAS and not self._descartando:
            self.saida.append("<br>")

    def handle_endtag(self, tag):
        if tag in TAGS_DESCARTADAS:
            if self._descartando:
                self._descartando -= 1
            return
        if self._descartando:
            return
        if tag == "a" and self.pilha and self.pilha[-1] == "a-ignorado":
            self.pilha.pop()
            return
        if tag in {"div", "section", "article"}:
            self._fechar("p")
            return
        if tag in TAGS_PERMITIDAS and tag not in TAGS_VAZIAS:
            self._fechar(tag)

    def handle_data(self, dados):
        if not self._descartando:
            self.saida.append(escape(dados, quote=False))

    def resultado(self):
        while self.pilha:
            aberta = self.pilha.pop()
            if aberta != "a-ignorado":
                self.saida.append(f"</{aberta}>")
        html = "".join(self.saida)
        html = re.sub(r"<(p|li|h2|h3|h4|blockquote|strong|em|b|i|u)>\s*</\1>", "", html)
        return html.strip()


def sanitizar_html(html):
    """Converte HTML externo em HTML seguro para `dangerouslySetInnerHTML`.

    Sem imagens, iframes, scripts, estilos ou atributos de evento. Links so http/https
    e sempre abrindo em nova aba com rel="noopener noreferrer nofollow".
    Se o resultado nao tiver nenhum bloco, o texto e embrulhado em paragrafos.
    """
    if not html or not str(html).strip():
        return ""
    sanitizador = _Sanitizador()
    try:
        sanitizador.feed(str(html))
        sanitizador.close()
        seguro = sanitizador.resultado()
    except Exception:
        seguro = ""
    if not texto_limpo(seguro):
        texto = texto_limpo(html)
        return f"<p>{escape(texto, quote=False)}</p>" if texto else ""
    if not re.search(r"<(p|ul|ol|blockquote|h2|h3|h4)>", seguro):
        blocos = [b.strip() for b in re.split(r"(?:<br>\s*){2,}", seguro) if b.strip()]
        seguro = "".join(f"<p>{bloco}</p>" for bloco in blocos)
    return seguro
