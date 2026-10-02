"""Leitura de feeds RSS 2.0, RSS 1.0 (RDF), Atom, JSON Feed e APIs JSON.

Somente biblioteca padrao: sem Django, sem rede. Recebe bytes/dicionarios e devolve
uma lista de `ItemFeed`. Quem baixa o conteudo e o `cliente.py`.
"""
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from html.entities import name2codepoint

from .texto import imagem_util

NS_CONTENT = "http://purl.org/rss/1.0/modules/content/"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_MEDIA = "http://search.yahoo.com/mrss/"
NS_ATOM = "http://www.w3.org/2005/Atom"
NS_ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

EXTENSOES_IMAGEM = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif")
ENTIDADES_XML = {"amp", "lt", "gt", "quot", "apos"}


class ErroFeed(Exception):
    """O conteudo recebido nao e um feed/API valido."""


@dataclass
class ItemFeed:
    titulo: str
    url: str
    id_externo: str = ""
    resumo: str = ""
    conteudo: str = ""
    imagem: str = ""
    autor: str = ""
    categorias: list = field(default_factory=list)
    publicado_em: datetime = None
    atualizado_em: datetime = None


# ------------------------------------------------------------------ datas

def interpretar_data(valor):
    """Aceita RFC 822 (RSS), ISO 8601 (Atom/JSON) e timestamp. Devolve datetime em UTC."""
    if valor in (None, ""):
        return None
    if isinstance(valor, (int, float)):
        try:
            return datetime.fromtimestamp(valor, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    texto = str(valor).strip()
    data = None
    try:
        data = parsedate_to_datetime(texto)
    except (TypeError, ValueError, IndexError):
        data = None
    if data is None:
        iso = texto.replace("Z", "+00:00").replace("z", "+00:00")
        iso = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", iso)  # -0300 -> -03:00
        try:
            data = datetime.fromisoformat(iso)
        except ValueError:
            return None
    if data.tzinfo is None:
        data = data.replace(tzinfo=timezone.utc)
    return data.astimezone(timezone.utc)


# ------------------------------------------------------------------ XML

def _nome(elemento):
    return elemento.tag.rsplit("}", 1)[-1] if isinstance(elemento.tag, str) else ""


def _ns(elemento):
    if isinstance(elemento.tag, str) and elemento.tag.startswith("{"):
        return elemento.tag[1:].split("}", 1)[0]
    return ""


def _filhos(elemento, nome, ns=None):
    return [
        filho for filho in elemento
        if _nome(filho) == nome and (ns is None or _ns(filho) == ns)
    ]


def _texto(elemento, nome, ns=None):
    for filho in _filhos(elemento, nome, ns):
        texto = "".join(filho.itertext()).strip()
        if texto:
            return texto
    return ""


def _corrigir_entidades(texto):
    """Troca entidades HTML (&nbsp;, &eacute;...) por numericas, que o XML aceita."""
    def trocar(resultado):
        nome = resultado.group(1)
        if nome in ENTIDADES_XML:
            return resultado.group(0)
        if nome in name2codepoint:
            return f"&#{name2codepoint[nome]};"
        return f"&amp;{nome};"

    return re.sub(r"&([a-zA-Z][a-zA-Z0-9]*);", trocar, texto)


def _carregar_xml(conteudo, codificacao=None):
    if isinstance(conteudo, str):
        conteudo = conteudo.encode("utf-8")
    conteudo = conteudo.lstrip(b"\xef\xbb\xbf \t\r\n")
    if not conteudo:
        raise ErroFeed("Resposta vazia.")
    # defesa extra contra expansao de entidades (billion laughs / XXE)
    if b"<!ENTITY" in conteudo[:4096].upper():
        raise ErroFeed("Feed com declaracao de entidades nao e aceito por seguranca.")
    try:
        return ET.fromstring(conteudo)
    except ET.ParseError:
        pass
    # segunda tentativa: decodifica, corrige entidades HTML e remove a declaracao XML
    texto = conteudo.decode(codificacao or "utf-8", errors="replace")
    texto = re.sub(r"^\s*<\?xml[^>]*\?>", "", texto)
    texto = _corrigir_entidades(texto)
    texto = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", texto)
    try:
        return ET.fromstring(texto)
    except ET.ParseError as erro:
        raise ErroFeed(f"XML invalido: {erro}") from erro


def _parece_imagem(url, tipo="", meio=""):
    if meio == "image" or (tipo or "").startswith("image/"):
        return True
    caminho = (url or "").split("?", 1)[0].lower()
    return caminho.endswith(EXTENSOES_IMAGEM)


_ATRIBUTOS_IMAGEM = ("data-echo", "data-src", "data-lazy-src", "data-original", "src")


def _atributo(tag, nome):
    achado = re.search(
        r"(?<![\w-])" + re.escape(nome) + r"\s*=\s*(?:\"([^\"]*)\"|'([^']*)')", tag, re.I)
    return unescape((achado.group(1) or achado.group(2) or "").strip()) if achado else ""


def _imagem_no_html(html):
    """Primeira imagem de verdade do HTML: pula logos, pixels e reservas de carregamento.

    Imagens com carregamento preguicoso guardam a URL real em data-echo/data-src.
    """
    for tag in re.findall(r"<img\b[^>]*>", html or "", re.I):
        alt = _atributo(tag, "alt")
        estilo = _atributo(tag, "style")
        for nome in _ATRIBUTOS_IMAGEM:
            url = _atributo(tag, nome)
            if url and imagem_util(url, alt, estilo):
                return url
    return ""


def _imagem_destaque(item):
    """Tag propria de alguns feeds (ex.: <imagem-destaque> da Agencia Brasil)."""
    for nome in ("imagem-destaque", "imagem_destaque", "featured-image", "featured_image"):
        for filho in _filhos(item, nome):
            url = (filho.get("url") or filho.get("href") or "".join(filho.itertext())).strip()
            if url and imagem_util(url):
                return url
    return ""


def _imagem_media(item):
    """media:content / media:thumbnail / media:group / enclosure / itunes:image."""
    candidatos = []
    grupos = [item] + _filhos(item, "group", NS_MEDIA)
    for grupo in grupos:
        for midia in _filhos(grupo, "content", NS_MEDIA):
            url = midia.get("url", "")
            if url and _parece_imagem(url, midia.get("type", ""), midia.get("medium", "")):
                largura = int(midia.get("width") or 0) if str(midia.get("width") or "").isdigit() else 0
                candidatos.append((largura, url))
        for miniatura in _filhos(grupo, "thumbnail", NS_MEDIA):
            if miniatura.get("url"):
                candidatos.append((0, miniatura.get("url")))
    if candidatos:
        # prefere a maior imagem declarada
        return sorted(candidatos, key=lambda par: par[0], reverse=True)[0][1]
    for anexo in _filhos(item, "enclosure"):
        url = anexo.get("url", "")
        if url and _parece_imagem(url, anexo.get("type", "")):
            return url
    for imagem in _filhos(item, "image", NS_ITUNES):
        if imagem.get("href"):
            return imagem.get("href")
    return ""


def _item_rss(item):
    titulo = _texto(item, "title")
    link = _texto(item, "link")
    if not link:
        # alguns feeds usam atom:link dentro do item
        for atom in _filhos(item, "link", NS_ATOM):
            if atom.get("href"):
                link = atom.get("href")
                break
    guid = _texto(item, "guid") or item.get(f"{{{NS_RDF}}}about", "")
    if not link and guid.startswith("http"):
        link = guid
    resumo = _texto(item, "description")
    conteudo = _texto(item, "encoded", NS_CONTENT)
    imagem = (
        _imagem_media(item) or _imagem_destaque(item)
        or _imagem_no_html(conteudo) or _imagem_no_html(resumo)
    )
    categorias = [
        "".join(c.itertext()).strip() for c in _filhos(item, "category") + _filhos(item, "subject", NS_DC)
    ]
    return ItemFeed(
        titulo=titulo,
        url=link.strip(),
        id_externo=guid.strip(),
        resumo=resumo,
        conteudo=conteudo,
        imagem=imagem.strip(),
        autor=_texto(item, "creator", NS_DC) or _texto(item, "author"),
        categorias=[c for c in categorias if c],
        publicado_em=interpretar_data(_texto(item, "pubDate") or _texto(item, "date", NS_DC)),
        atualizado_em=interpretar_data(_texto(item, "updated", NS_ATOM)),
    )


def _link_atom(entrada):
    alternativo = ""
    for link in _filhos(entrada, "link", NS_ATOM):
        rel = link.get("rel", "alternate")
        if rel == "alternate" and link.get("href"):
            if not alternativo or link.get("type", "text/html") == "text/html":
                alternativo = link.get("href")
    return alternativo


def _item_atom(entrada):
    resumo = _texto(entrada, "summary", NS_ATOM)
    conteudo = _texto(entrada, "content", NS_ATOM)
    imagem = _imagem_media(entrada)
    if not imagem:
        for link in _filhos(entrada, "link", NS_ATOM):
            if link.get("rel") == "enclosure" and _parece_imagem(link.get("href"), link.get("type", "")):
                imagem = link.get("href")
                break
    imagem = imagem or _imagem_no_html(conteudo) or _imagem_no_html(resumo)
    autores = [
        _texto(autor, "name", NS_ATOM) for autor in _filhos(entrada, "author", NS_ATOM)
    ]
    categorias = [
        c.get("label") or c.get("term") or "" for c in _filhos(entrada, "category", NS_ATOM)
    ]
    publicado = _texto(entrada, "published", NS_ATOM)
    atualizado = _texto(entrada, "updated", NS_ATOM)
    return ItemFeed(
        titulo=_texto(entrada, "title", NS_ATOM),
        url=_link_atom(entrada).strip(),
        id_externo=_texto(entrada, "id", NS_ATOM),
        resumo=resumo,
        conteudo=conteudo,
        imagem=(imagem or "").strip(),
        autor=", ".join(a for a in autores if a),
        categorias=[c for c in categorias if c],
        publicado_em=interpretar_data(publicado or atualizado),
        atualizado_em=interpretar_data(atualizado),
    )


def interpretar_xml(conteudo, codificacao=None):
    raiz = _carregar_xml(conteudo, codificacao)
    nome = _nome(raiz).lower()
    if nome == "rss":
        canal = next(iter(_filhos(raiz, "channel")), None)
        if canal is None:
            raise ErroFeed("RSS sem <channel>.")
        return [_item_rss(item) for item in _filhos(canal, "item")]
    if nome == "rdf":  # RSS 1.0
        return [_item_rss(item) for item in raiz if _nome(item) == "item"]
    if nome == "feed":  # Atom
        return [_item_atom(entrada) for entrada in _filhos(raiz, "entry", NS_ATOM)]
    raise ErroFeed(f"Formato XML nao reconhecido (<{_nome(raiz)}>).")


# ------------------------------------------------------------------ JSON

def _carregar_json(conteudo):
    if isinstance(conteudo, (dict, list)):
        return conteudo
    if isinstance(conteudo, bytes):
        conteudo = conteudo.decode("utf-8-sig", errors="replace")
    try:
        return json.loads(conteudo)
    except (TypeError, ValueError) as erro:
        raise ErroFeed(f"JSON invalido: {erro}") from erro


def interpretar_json_feed(conteudo):
    """JSON Feed 1.0/1.1 (https://jsonfeed.org)."""
    dados = _carregar_json(conteudo)
    if not isinstance(dados, dict) or not isinstance(dados.get("items"), list):
        raise ErroFeed("JSON Feed sem a lista 'items'.")
    itens = []
    for bruto in dados["items"]:
        if not isinstance(bruto, dict):
            continue
        autores = bruto.get("authors") or ([bruto["author"]] if bruto.get("author") else [])
        nomes = [a.get("name", "") for a in autores if isinstance(a, dict)]
        itens.append(ItemFeed(
            titulo=str(bruto.get("title") or ""),
            url=str(bruto.get("url") or bruto.get("external_url") or ""),
            id_externo=str(bruto.get("id") or ""),
            resumo=str(bruto.get("summary") or ""),
            conteudo=str(bruto.get("content_html") or bruto.get("content_text") or ""),
            imagem=str(bruto.get("image") or bruto.get("banner_image") or ""),
            autor=", ".join(n for n in nomes if n),
            categorias=[str(t) for t in bruto.get("tags") or [] if t],
            publicado_em=interpretar_data(bruto.get("date_published")),
            atualizado_em=interpretar_data(bruto.get("date_modified")),
        ))
    return itens


def valor_por_caminho(dados, caminho):
    """Le 'a.b.0.c' de dicionarios/listas. Caminho vazio devolve o proprio dado."""
    if not caminho:
        return dados
    atual = dados
    for parte in str(caminho).split("."):
        if isinstance(atual, dict):
            atual = atual.get(parte)
        elif isinstance(atual, list) and parte.isdigit() and int(parte) < len(atual):
            atual = atual[int(parte)]
        else:
            return None
        if atual is None:
            return None
    return atual


def _como_texto(valor):
    if valor is None:
        return ""
    if isinstance(valor, dict):
        return str(valor.get("name") or valor.get("nome") or valor.get("url") or "")
    if isinstance(valor, list):
        return ", ".join(_como_texto(v) for v in valor if v)
    return str(valor)


def interpretar_api_json(conteudo, mapeamento):
    """API JSON generica. `mapeamento` diz onde esta cada campo, por exemplo:

    {"itens": "articles", "titulo": "title", "url": "url", "resumo": "description",
     "imagem": "urlToImage", "data": "publishedAt", "autor": "author",
     "id": "url", "categorias": "section"}
    """
    mapeamento = mapeamento or {}
    dados = _carregar_json(conteudo)
    lista = valor_por_caminho(dados, mapeamento.get("itens", ""))
    if not isinstance(lista, list):
        raise ErroFeed("O caminho 'itens' do mapeamento nao aponta para uma lista.")
    itens = []
    for bruto in lista:
        if not isinstance(bruto, dict):
            continue
        campo = lambda nome: valor_por_caminho(bruto, mapeamento.get(nome, nome))  # noqa: E731
        categorias = campo("categorias")
        if isinstance(categorias, str):
            categorias = [categorias]
        itens.append(ItemFeed(
            titulo=_como_texto(campo("titulo")),
            url=_como_texto(campo("url")),
            id_externo=_como_texto(campo("id")),
            resumo=_como_texto(campo("resumo")),
            conteudo=_como_texto(campo("conteudo")),
            imagem=_como_texto(campo("imagem")),
            autor=_como_texto(campo("autor")),
            categorias=[_como_texto(c) for c in (categorias or []) if c],
            publicado_em=interpretar_data(campo("data")),
            atualizado_em=interpretar_data(campo("atualizado")),
        ))
    return itens


def interpretar(conteudo, tipo="RSS", mapeamento=None, codificacao=None):
    """Ponto de entrada unico usado pelo servico de sincronizacao."""
    if tipo == "JSON_FEED":
        return interpretar_json_feed(conteudo)
    if tipo == "API_JSON":
        return interpretar_api_json(conteudo, mapeamento)
    return interpretar_xml(conteudo, codificacao)
