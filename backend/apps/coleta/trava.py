"""Trava que impede duas coletas ao mesmo tempo, em qualquer processo.

Antes a trava ficava so no cache. Sem Redis (o padrao em desenvolvimento) o cache e
local de cada processo, entao o worker do Celery, o comando manual e o painel nao se
enxergavam e podiam coletar juntos. Agora a trava usa o proprio sistema:

    COLETA_TRAVA_BACKEND=auto     (padrao) PostgreSQL -> "banco"; outros bancos -> "arquivo"
    COLETA_TRAVA_BACKEND=banco    advisory lock do PostgreSQL: vale entre maquinas que usam
                                  o mesmo banco e e liberado sozinho se o processo morrer
    COLETA_TRAVA_BACKEND=arquivo  lock de arquivo do sistema operacional (Linux e Windows):
                                  vale entre processos da mesma maquina e tambem e liberado
                                  sozinho se o processo morrer
    COLETA_TRAVA_BACKEND=cache    cache.add com expiracao (precisa do Redis entre processos);
                                  use so se o banco estiver atras de um pooler em modo
                                  transacao (ex.: PgBouncer), onde o advisory lock nao serve

Uso:
    with trava_coleta() as obtida:
        if not obtida:
            ...  # outra coleta em andamento
"""
import hashlib
import logging
import os
import uuid
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("apps.coleta")

CHAVE_TRAVA = "coleta:em-execucao"


def _config(nome, padrao):
    return getattr(settings, nome, padrao)


class TravaBanco:
    """pg_try_advisory_lock: nao bloqueia; a trava vive na sessao da conexao."""

    def __init__(self, nome=CHAVE_TRAVA):
        resumo = hashlib.sha256(f"pauta:{nome}".encode()).digest()[:8]
        self.chave = int.from_bytes(resumo, "big", signed=True)
        self.conexao = None

    def adquirir(self):
        from django.db import connection

        self.conexao = connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(%s)", [self.chave])
            return bool(cursor.fetchone()[0])

    def liberar(self):
        try:
            with self.conexao.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [self.chave])
        except Exception:  # conexao caiu: o PostgreSQL ja liberou a trava sozinho
            logger.warning("Nao foi possivel liberar a trava no banco.", exc_info=True)


class TravaArquivo:
    """flock (Linux/macOS) ou msvcrt.locking (Windows) num arquivo sem conteudo util."""

    def __init__(self, caminho=None):
        self.caminho = Path(caminho or _config("COLETA_TRAVA_ARQUIVO", "")
                            or Path(settings.BASE_DIR) / ".coleta.lock")
        self.descritor = None

    def adquirir(self):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        descritor = os.open(self.caminho, os.O_RDWR | os.O_CREAT, 0o644)
        try:
            if os.name == "nt":
                import msvcrt

                os.lseek(descritor, 0, os.SEEK_SET)
                msvcrt.locking(descritor, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(descritor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(descritor)
            return False
        self.descritor = descritor
        return True

    def liberar(self):
        if self.descritor is None:
            return
        try:
            if os.name == "nt":
                import msvcrt

                os.lseek(self.descritor, 0, os.SEEK_SET)
                msvcrt.locking(self.descritor, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.descritor, fcntl.LOCK_UN)
        finally:
            os.close(self.descritor)
            self.descritor = None


class TravaCache:
    """cache.add com dono: so quem adquiriu apaga (evita apagar a trava de outra coleta)."""

    def __init__(self):
        self.token = uuid.uuid4().hex

    def adquirir(self):
        duracao = int(_config("COLETA_TRAVA_SEGUNDOS", 30 * 60))
        return cache.add(CHAVE_TRAVA, self.token, duracao)

    def liberar(self):
        if cache.get(CHAVE_TRAVA) == self.token:
            cache.delete(CHAVE_TRAVA)


def criar_trava():
    tipo = str(_config("COLETA_TRAVA_BACKEND", "auto")).strip().lower()
    if tipo == "auto":
        from django.db import connection

        tipo = "banco" if connection.vendor == "postgresql" else "arquivo"
    if tipo == "banco":
        return TravaBanco()
    if tipo == "arquivo":
        return TravaArquivo()
    if tipo == "cache":
        return TravaCache()
    raise ValueError(f"COLETA_TRAVA_BACKEND invalido: {tipo!r} (use auto, banco, arquivo ou cache)")


@contextmanager
def trava_coleta():
    """Tenta pegar a trava sem esperar. Devolve True/False e sempre libera no fim."""
    trava = criar_trava()
    obtida = trava.adquirir()
    try:
        yield obtida
    finally:
        if obtida:
            trava.liberar()
