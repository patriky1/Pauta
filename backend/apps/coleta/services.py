"""Sincronizacao das fontes externas.

Fluxo de cada fonte:
    baixar (HTTP condicional) -> interpretar -> preparar/normalizar -> deduplicar
    -> categorizar -> gravar (cada item na propria transacao) -> registrar log.

Garantias:
- Idempotente: rodar duas vezes seguidas nao cria nem altera nada.
- Duplicatas bloqueadas por (fonte, id externo), URL normalizada e hash do titulo,
  alem de restricoes unicas no banco.
- Uma fonte (ou um item) com erro nao interrompe as demais.
"""
import logging
import os
from dataclasses import dataclass, field
from datetime import timedelta
from html import escape

from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from apps.categories.models import Categoria
from apps.news.models import Noticia, StatusNoticia

from . import parser
from .categorizacao import Categorizador
from .cliente import ConfigHttp, ErroColeta, LeitorPaginas, baixar
from .models import ExecucaoColeta, FonteNoticia, MapeamentoCategoria, RegraCategorizacao
from .texto import (
    gerar_hash,
    imagem_util,
    normalizar_texto,
    normalizar_url,
    resumir,
    sanitizar_html,
    texto_limpo,
    url_segura,
)

logger = logging.getLogger("apps.coleta")

CHAVE_TRAVA = "coleta:em-execucao"

NOVA, ATUALIZADA, IGNORADA = "nova", "atualizada", "ignorada"


def _config(nome, padrao):
    return getattr(settings, nome, padrao)


def config_http():
    return ConfigHttp(
        user_agent=_config("COLETA_USER_AGENT", "PautaBot/1.0"),
        timeout_conexao=float(_config("COLETA_TIMEOUT_CONEXAO", 5)),
        timeout_leitura=float(_config("COLETA_TIMEOUT_LEITURA", 20)),
        limite_bytes=int(float(_config("COLETA_TAMANHO_MAXIMO_MB", 5)) * 1024 * 1024),
        permitir_rede_interna=bool(_config("COLETA_PERMITIR_REDE_INTERNA", False)),
    )


def obter_autor_padrao():
    """Conta tecnica que assina as noticias importadas (campo autor e obrigatorio).

    Nao consegue fazer login (senha inutilizavel) e tem papel USUARIO, entao nao aparece
    na lista de autores da redacao. O nome do autor real fica em `autor_original`.
    """
    from apps.users.models import TipoUsuario, User

    username = _config("COLETA_USUARIO", "coleta-automatica")
    usuario = User.objects.filter(username=username).first()
    if usuario:
        return usuario
    usuario = User(
        username=username,
        email=f"{username}@coleta.invalid",
        nome=_config("COLETA_NOME_AUTOR", "Agregador Pauta"),
        tipo_usuario=TipoUsuario.USUARIO,
    )
    usuario.set_unusable_password()
    try:
        with transaction.atomic():
            usuario.save()
    except IntegrityError:  # criado em paralelo por outro processo
        usuario = User.objects.get(username=username)
    return usuario


# ------------------------------------------------------------------ download

def _parametros_autenticacao(fonte):
    """Le a chave da API do ambiente. Devolve (params, headers)."""
    if not fonte.chave_api_variavel:
        return None, None
    chave = os.environ.get(fonte.chave_api_variavel, "")
    if not chave:
        raise ErroColeta(
            f"A variavel de ambiente {fonte.chave_api_variavel} nao esta definida."
        )
    destino = (fonte.chave_api_parametro or "apiKey").strip()
    if destino.lower().startswith("header:"):
        return None, {destino.split(":", 1)[1].strip(): chave}
    return {destino: chave}, None


def obter_itens(fonte):
    """Baixa e interpreta a fonte. Devolve (itens, resposta)."""
    parametros, cabecalhos = _parametros_autenticacao(fonte)
    resposta = baixar(
        fonte.url_feed, config_http(),
        etag=fonte.etag, ultima_modificacao=fonte.ultima_modificacao,
        parametros=parametros, cabecalhos=cabecalhos,
    )
    if resposta.nao_modificado:
        return [], resposta
    itens = parser.interpretar(
        resposta.conteudo, fonte.tipo, fonte.mapeamento_json, resposta.codificacao,
    )
    return itens, resposta


# ------------------------------------------------------------------ categorizacao

def montar_categorizador(fonte):
    mapeamentos = [
        (fonte_id == fonte.pk, termo, categoria_id)
        for fonte_id, termo, categoria_id in MapeamentoCategoria.objects.filter(
            Q(fonte=fonte) | Q(fonte__isnull=True)
        ).values_list("fonte_id", "termo_origem", "categoria_id")
    ]
    return Categorizador.montar(
        categoria_padrao=fonte.categoria_padrao_id,
        mapeamentos=mapeamentos,
        categorias=Categoria.objects.filter(ativa=True).values_list("id", "nome", "slug"),
        regras=RegraCategorizacao.objects.filter(
            ativa=True, categoria__ativa=True
        ).values_list("categoria_id", "palavras_chave", "peso"),
        pontuacao_minima=int(_config("COLETA_PONTUACAO_MINIMA", 2)),
    )


# ------------------------------------------------------------------ preparo e gravacao

@dataclass
class ItemPreparado:
    item: parser.ItemFeed
    titulo: str
    url: str
    id_externo: str
    hash: str
    resumo: str
    corpo: str
    imagem: str
    autor: str
    publicado_em: object
    atualizado_em: object


def preparar(fonte, item):
    """Normaliza o item do feed. Devolve None se nao der para aproveitar."""
    titulo = resumir(texto_limpo(item.titulo), 200)
    url = normalizar_url(item.url)
    if not titulo or not url:
        return None
    texto_resumo = texto_limpo(item.resumo) or texto_limpo(item.conteudo)
    resumo = resumir(texto_resumo, 480)
    if fonte.importar_conteudo_completo and item.conteudo:
        corpo = sanitizar_html(item.conteudo)
    else:
        corpo = sanitizar_html(item.resumo) if item.resumo else ""
    if not corpo:
        corpo = f"<p>{escape(resumo or titulo, quote=False)}</p>"
    return ItemPreparado(
        item=item,
        titulo=titulo,
        url=url,
        id_externo=(item.id_externo or "").strip()[:500] or url[:500],
        hash=gerar_hash(fonte.pk, normalizar_texto(titulo)),
        resumo=resumo,
        corpo=corpo,
        imagem=(url_segura(item.imagem) if imagem_util(item.imagem) else "")[:1000],
        autor=resumir(texto_limpo(item.autor), 200),
        publicado_em=item.publicado_em,
        atualizado_em=item.atualizado_em,
    )


@dataclass
class IndiceExistentes:
    por_id: dict = field(default_factory=dict)
    por_url: dict = field(default_factory=dict)
    por_hash: dict = field(default_factory=dict)

    def registrar(self, noticia):
        if noticia.id_externo and noticia.fonte_externa_id:
            self.por_id[(noticia.fonte_externa_id, noticia.id_externo)] = noticia
        if noticia.url_original:
            self.por_url[noticia.url_original] = noticia
        if noticia.hash_conteudo:
            self.por_hash[noticia.hash_conteudo] = noticia

    def buscar(self, fonte, preparado):
        return (
            self.por_id.get((fonte.pk, preparado.id_externo))
            or self.por_url.get(preparado.url)
            or self.por_hash.get(preparado.hash)
        )


def indexar_existentes(fonte, preparados):
    """Uma unica consulta traz tudo o que ja existe entre os itens do feed."""
    indice = IndiceExistentes()
    if not preparados:
        return indice
    consulta = Noticia.objects.select_related(None).prefetch_related(None).filter(
        Q(fonte_externa=fonte, id_externo__in=[p.id_externo for p in preparados])
        | Q(url_original__in=[p.url for p in preparados])
        | Q(hash_conteudo__in=[p.hash for p in preparados])
    )
    for noticia in consulta:
        indice.registrar(noticia)
    return indice


def _atualizar(existente, fonte, preparado):
    """So atualiza se a fonte informar uma data de modificacao mais nova que a nossa.

    Assim uma correcao feita pela redacao no painel nao e desfeita na proxima coleta,
    e repetir a coleta nao muda nada (idempotencia).
    """
    momento = preparado.atualizado_em or preparado.publicado_em
    if not momento or not existente.atualizado_em or momento <= existente.atualizado_em:
        return IGNORADA
    novos = {
        "titulo": preparado.titulo,
        "resumo": preparado.resumo,
        "conteudo": preparado.corpo,
        "autor_original": preparado.autor,
    }
    if preparado.imagem:
        novos["imagem_url"] = preparado.imagem
    alterados = [campo for campo, valor in novos.items() if getattr(existente, campo) != valor]
    if not alterados:
        return IGNORADA
    for campo in alterados:
        setattr(existente, campo, novos[campo])
    existente.hash_conteudo = preparado.hash
    existente.save(update_fields=alterados + [
        "hash_conteudo", "tempo_leitura", "data_atualizacao", "atualizado_em",
    ])
    return ATUALIZADA


def gravar(fonte, preparado, *, categorizador, indice, autor, limite_idade, leitor=None):
    existente = indice.buscar(fonte, preparado)
    if existente is not None:
        if existente.fonte_externa_id != fonte.pk:
            return IGNORADA  # mesma materia ja veio por outra fonte
        return _atualizar(existente, fonte, preparado)

    agora = timezone.now()
    publicado = preparado.publicado_em or preparado.atualizado_em
    if publicado and publicado < limite_idade:
        return IGNORADA  # antiga demais (evita despejar o arquivo inteiro do feed)

    imagem = preparado.imagem
    if not imagem and leitor is not None and fonte.buscar_imagem_na_pagina:
        try:
            imagem = leitor.imagem(preparado.url)[:1000]
        except Exception:  # imagem e opcional: nunca derruba o item
            logger.debug("Sem imagem na pagina %s", preparado.url, exc_info=True)
            imagem = ""

    categoria_id, motivo = categorizador.categorizar(
        preparado.titulo, preparado.resumo, preparado.item.categorias,
    )
    noticia = Noticia(
        titulo=preparado.titulo,
        resumo=preparado.resumo,
        conteudo=preparado.corpo,
        imagem_url=imagem,
        imagem_credito=f"Imagem: {fonte.nome}"[:120] if imagem else "",
        autor=autor,
        categoria_id=categoria_id,
        status=StatusNoticia.PUBLICADA if fonte.publicar_automaticamente else StatusNoticia.REVISAO,
        data_publicacao=min(publicado, agora) if publicado else agora,
        fonte_externa=fonte,
        url_original=preparado.url,
        id_externo=preparado.id_externo,
        hash_conteudo=preparado.hash,
        autor_original=preparado.autor,
    )
    try:
        with transaction.atomic():
            noticia.save()
    except IntegrityError:
        # outra execucao gravou a mesma noticia entre a consulta e o insert
        logger.info("Duplicata barrada pelo banco: %s", preparado.url)
        return IGNORADA
    indice.registrar(noticia)
    logger.debug("Nova noticia %s (categoria por %s)", noticia.slug, motivo)
    return NOVA


def sincronizar_fonte(fonte, *, autor=None, leitor=None):
    """Sincroniza uma fonte e devolve o `ExecucaoColeta` com o resultado.

    Nunca levanta excecao: qualquer falha fica registrada no log e na propria fonte.
    """
    execucao = ExecucaoColeta.objects.create(fonte=fonte)
    contagem = {NOVA: 0, ATUALIZADA: 0, IGNORADA: 0}
    erros = []
    try:
        autor = autor or obter_autor_padrao()
        itens, resposta = obter_itens(fonte)
        if resposta.nao_modificado:
            execucao.mensagem = "Sem novidades desde a ultima coleta (HTTP 304)."
        else:
            itens = itens[: max(int(fonte.limite_por_coleta or 30), 1)]
            execucao.itens_lidos = len(itens)
            preparados = []
            for item in itens:
                preparado = preparar(fonte, item)
                if preparado is None:
                    contagem[IGNORADA] += 1
                else:
                    preparados.append(preparado)
            categorizador = montar_categorizador(fonte)
            indice = indexar_existentes(fonte, preparados)
            limite_idade = timezone.now() - timedelta(
                days=int(_config("COLETA_IDADE_MAXIMA_DIAS", 7)))
            for preparado in preparados:
                try:
                    acao = gravar(
                        fonte, preparado, categorizador=categorizador, indice=indice,
                        autor=autor, limite_idade=limite_idade, leitor=leitor,
                    )
                except Exception as erro:  # um item ruim nao derruba a fonte
                    logger.exception("Erro ao gravar item de %s: %s", fonte.nome, preparado.url)
                    erros.append(f"{preparado.titulo[:80]}: {erro}")
                    continue
                contagem[acao] += 1
        fonte.etag = resposta.etag
        fonte.ultima_modificacao = resposta.ultima_modificacao
        fonte.ultimo_sucesso = timezone.now()
        fonte.erros_consecutivos = 0
        fonte.ultimo_erro = "\n".join(erros)[:2000]
        execucao.status = ExecucaoColeta.Status.PARCIAL if erros else ExecucaoColeta.Status.SUCESSO
    except (ErroColeta, parser.ErroFeed) as erro:
        logger.warning("Fonte %s falhou: %s", fonte.nome, erro)
        execucao.status = ExecucaoColeta.Status.ERRO
        execucao.mensagem = str(erro)[:2000]
        fonte.erros_consecutivos += 1
        fonte.ultimo_erro = str(erro)[:2000]
    except Exception as erro:  # erro inesperado: registra com traceback e segue
        logger.exception("Erro inesperado na fonte %s", fonte.nome)
        execucao.status = ExecucaoColeta.Status.ERRO
        execucao.mensagem = f"Erro inesperado: {erro}"[:2000]
        fonte.erros_consecutivos += 1
        fonte.ultimo_erro = execucao.mensagem

    agora = timezone.now()
    execucao.novas = contagem[NOVA]
    execucao.atualizadas = contagem[ATUALIZADA]
    execucao.ignoradas = contagem[IGNORADA]
    if erros:
        execucao.mensagem = ("\n".join(erros))[:2000]
    execucao.finalizada_em = agora
    fonte.ultima_sincronizacao = agora
    fonte.total_importadas += contagem[NOVA]
    try:
        execucao.save()
        fonte.save(update_fields=[
            "ultima_sincronizacao", "ultimo_sucesso", "ultimo_erro", "erros_consecutivos",
            "total_importadas", "etag", "ultima_modificacao", "atualizado_em",
        ])
    except Exception:
        logger.exception("Nao foi possivel salvar o estado da fonte %s", fonte.nome)
    logger.info(
        "Coleta %s: %s (lidos=%s novas=%s atualizadas=%s ignoradas=%s)",
        fonte.nome, execucao.status, execucao.itens_lidos, execucao.novas,
        execucao.atualizadas, execucao.ignoradas,
    )
    if contagem[NOVA] or contagem[ATUALIZADA]:
        from apps.news.services import invalidar_carrossel

        invalidar_carrossel()
    return execucao


def limpar_execucoes_antigas():
    dias = int(_config("COLETA_RETENCAO_LOGS_DIAS", 30))
    limite = timezone.now() - timedelta(days=dias)
    apagadas, _ = ExecucaoColeta.objects.filter(iniciada_em__lt=limite).delete()
    return apagadas


def sincronizar_todas(fontes=None):
    """Sincroniza todas as fontes ativas (ou as informadas).

    Usa uma trava no cache para impedir duas coletas simultaneas. Em producao o cache
    deve ser o Redis (REDIS_URL) para a trava valer entre processos.
    """
    duracao_trava = int(_config("COLETA_TRAVA_SEGUNDOS", 30 * 60))
    if not cache.add(CHAVE_TRAVA, timezone.now().isoformat(), duracao_trava):
        logger.warning("Coleta ignorada: ja existe outra em andamento.")
        return {"executada": False, "motivo": "Outra coleta ja esta em andamento."}

    resumo = {"executada": True, "fontes": 0, "erros": 0, "novas": 0, "atualizadas": 0,
              "ignoradas": 0, "detalhes": []}
    try:
        if fontes is None:
            fontes = FonteNoticia.objects.filter(ativa=True).select_related("categoria_padrao")
        autor = obter_autor_padrao()
        leitor = LeitorPaginas(config_http())
        for fonte in fontes:
            try:
                execucao = sincronizar_fonte(fonte, autor=autor, leitor=leitor)
            except Exception:  # defesa extra: sincronizar_fonte ja trata tudo
                logger.exception("Falha nao tratada na fonte %s", fonte)
                resumo["erros"] += 1
                continue
            resumo["fontes"] += 1
            resumo["novas"] += execucao.novas
            resumo["atualizadas"] += execucao.atualizadas
            resumo["ignoradas"] += execucao.ignoradas
            if execucao.status == ExecucaoColeta.Status.ERRO:
                resumo["erros"] += 1
            resumo["detalhes"].append({
                "fonte": fonte.nome, "status": execucao.status, "novas": execucao.novas,
                "atualizadas": execucao.atualizadas, "ignoradas": execucao.ignoradas,
                "mensagem": execucao.mensagem,
            })
        limpar_execucoes_antigas()
    finally:
        cache.delete(CHAVE_TRAVA)
    logger.info("Coleta concluida: %s fontes, %s novas, %s com erro",
                resumo["fontes"], resumo["novas"], resumo["erros"])
    return resumo
