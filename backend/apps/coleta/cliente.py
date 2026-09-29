"""Download de feeds e paginas, com limites de tempo, tamanho e destino.

Sem dependencia do Django: as configuracoes chegam por parametro (ver `ConfigHttp`).
"""
import ipaddress
import re
import socket
from dataclasses import dataclass
from html import unescape
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import requests

from .texto import imagem_util, url_segura

MAXIMO_REDIRECIONAMENTOS = 5


class ErroColeta(Exception):
    """Falha ao baixar o conteudo de uma fonte."""


@dataclass
class ConfigHttp:
    user_agent: str = "PautaBot/1.0"
    timeout_conexao: float = 5.0
    timeout_leitura: float = 20.0
    limite_bytes: int = 5 * 1024 * 1024
    permitir_rede_interna: bool = False


@dataclass
class RespostaHttp:
    conteudo: bytes = b""
    nao_modificado: bool = False
    etag: str = ""
    ultima_modificacao: str = ""
    tipo_conteudo: str = ""
    codificacao: str = ""
    url_final: str = ""


def verificar_destino(url, config):
    """Impede que a coleta acesse a rede interna do servidor (SSRF)."""
    if not url_segura(url):
        raise ErroColeta(f"URL recusada (apenas http/https): {url[:120]}")
    if config.permitir_rede_interna:
        return
    host = urlsplit(url).hostname or ""
    try:
        enderecos = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except socket.gaierror as erro:
        raise ErroColeta(f"Nao foi possivel resolver o endereco {host}.") from erro
    for endereco in enderecos:
        ip = ipaddress.ip_address(endereco.split("%", 1)[0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                or ip.is_multicast or ip.is_unspecified):
            raise ErroColeta(f"Destino {host} aponta para a rede interna e foi bloqueado.")


def baixar(url, config=None, *, etag="", ultima_modificacao="", parametros=None,
           cabecalhos=None, aceitar="application/rss+xml, application/atom+xml, "
                                   "application/xml, text/xml, application/json;q=0.9, */*;q=0.5"):
    """GET com requisicao condicional (ETag/Last-Modified), limite de tamanho e
    redirecionamentos verificados um a um."""
    config = config or ConfigHttp()
    enviar = {"User-Agent": config.user_agent, "Accept": aceitar,
              "Accept-Encoding": "gzip, deflate"}
    if etag:
        enviar["If-None-Match"] = etag
    if ultima_modificacao:
        enviar["If-Modified-Since"] = ultima_modificacao
    enviar.update(cabecalhos or {})

    atual = url
    for _ in range(MAXIMO_REDIRECIONAMENTOS + 1):
        verificar_destino(atual, config)
        try:
            resposta = requests.get(
                atual, headers=enviar, params=parametros, stream=True, allow_redirects=False,
                timeout=(config.timeout_conexao, config.timeout_leitura),
            )
        except requests.Timeout as erro:
            raise ErroColeta("Tempo esgotado ao acessar a fonte.") from erro
        except requests.RequestException as erro:
            raise ErroColeta(f"Falha de conexao: {erro.__class__.__name__}.") from erro

        if resposta.is_redirect or resposta.status_code in (301, 302, 303, 307, 308):
            destino = resposta.headers.get("Location", "")
            resposta.close()
            if not destino:
                raise ErroColeta("Redirecionamento sem destino.")
            atual = urljoin(atual, destino)
            parametros = None  # ja fazem parte da URL de destino
            continue
        break
    else:
        raise ErroColeta("Redirecionamentos demais.")

    try:
        if resposta.status_code == 304:
            return RespostaHttp(nao_modificado=True, etag=etag,
                                ultima_modificacao=ultima_modificacao, url_final=atual)
        if resposta.status_code >= 400:
            raise ErroColeta(f"A fonte respondeu HTTP {resposta.status_code}.")
        declarado = resposta.headers.get("Content-Length", "")
        if declarado.isdigit() and int(declarado) > config.limite_bytes:
            raise ErroColeta("Resposta maior que o limite configurado.")
        partes, total = [], 0
        for bloco in resposta.iter_content(chunk_size=64 * 1024):
            total += len(bloco)
            if total > config.limite_bytes:
                raise ErroColeta("Resposta maior que o limite configurado.")
            partes.append(bloco)
        tipo = resposta.headers.get("Content-Type", "")
        charset = re.search(r"charset=([\w-]+)", tipo, re.I)
        return RespostaHttp(
            conteudo=b"".join(partes),
            etag=resposta.headers.get("ETag", "")[:255],
            ultima_modificacao=resposta.headers.get("Last-Modified", "")[:100],
            tipo_conteudo=tipo,
            codificacao=charset.group(1) if charset else "",
            url_final=atual,
        )
    except requests.RequestException as erro:
        raise ErroColeta(f"Falha ao ler a resposta: {erro.__class__.__name__}.") from erro
    finally:
        resposta.close()


def extrair_imagem_de_pagina(html, base):
    """Le og:image / twitter:image do <head> da pagina."""
    for propriedade in ("og:image:secure_url", "og:image", "twitter:image", "twitter:image:src"):
        padrao = (
            r"<meta[^>]+(?:property|name)=[\"']" + re.escape(propriedade)
            + r"[\"'][^>]*content=[\"']([^\"']+)[\"']"
        )
        inverso = (
            r"<meta[^>]+content=[\"']([^\"']+)[\"'][^>]*(?:property|name)=[\"']"
            + re.escape(propriedade) + r"[\"']"
        )
        resultado = re.search(padrao, html, re.I) or re.search(inverso, html, re.I)
        if resultado:
            url = url_segura(urljoin(base, unescape(resultado.group(1).strip())))
            # og:image de muitos sites e o logo quando a materia nao tem foto
            if url and imagem_util(url):
                return url
    return ""


class LeitorPaginas:
    """Busca a imagem de destaque na pagina original quando o feed nao traz nenhuma.

    So e usado nas fontes com essa opcao ligada. Respeita o robots.txt de cada site
    e le no maximo 512 KB de cada pagina. Uma instancia por rodada de coleta.
    """

    LIMITE_PAGINA = 512 * 1024

    def __init__(self, config=None):
        self.config = config or ConfigHttp()
        self._robots = {}

    def permitido(self, url):
        partes = urlsplit(url)
        raiz = f"{partes.scheme}://{partes.netloc}"
        if raiz not in self._robots:
            leitor = RobotFileParser()
            try:
                resposta = baixar(f"{raiz}/robots.txt", self.config, aceitar="text/plain")
                leitor.parse(resposta.conteudo.decode("utf-8", errors="replace").splitlines())
            except ErroColeta:
                # sem robots.txt acessivel: segue a convencao de permitir
                leitor.parse([])
            self._robots[raiz] = leitor
        return self._robots[raiz].can_fetch(self.config.user_agent, url)

    def imagem(self, url):
        if not url_segura(url) or not self.permitido(url):
            return ""
        config = ConfigHttp(
            user_agent=self.config.user_agent,
            timeout_conexao=self.config.timeout_conexao,
            timeout_leitura=min(self.config.timeout_leitura, 10),
            limite_bytes=self.LIMITE_PAGINA,
            permitir_rede_interna=self.config.permitir_rede_interna,
        )
        try:
            resposta = baixar(url, config, aceitar="text/html")
        except ErroColeta:
            return ""
        html = resposta.conteudo.decode(resposta.codificacao or "utf-8", errors="replace")
        cabeca = html.split("</head>", 1)[0]
        return extrair_imagem_de_pagina(cabeca, resposta.url_final or url)
