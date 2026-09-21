"""Criacao de notificacoes a partir de eventos editoriais."""
from .models import Notificacao


def _criar_em_lote(usuarios_ids, **campos):
    Notificacao.objects.bulk_create(
        [Notificacao(usuario_id=uid, **campos) for uid in set(usuarios_ids)]
    )


def notificar_publicacao(noticia):
    from apps.interactions.models import AutorSeguido, CategoriaSeguida, TagSeguida

    url = f"/noticia/{noticia.slug}"
    por_categoria = CategoriaSeguida.objects.filter(
        categoria=noticia.categoria
    ).values_list("usuario_id", flat=True)
    _criar_em_lote(
        por_categoria,
        tipo=Notificacao.Tipo.CATEGORIA,
        titulo=f"Nova noticia sobre {noticia.categoria.nome}",
        mensagem=noticia.titulo[:300],
        url=url,
    )

    por_autor = AutorSeguido.objects.filter(autor=noticia.autor).values_list(
        "usuario_id", flat=True)
    _criar_em_lote(
        por_autor,
        tipo=Notificacao.Tipo.AUTOR,
        titulo=f"{noticia.autor.nome} publicou uma noticia",
        mensagem=noticia.titulo[:300],
        url=url,
    )

    por_tag = TagSeguida.objects.filter(tag__in=noticia.tags.all()).values_list(
        "usuario_id", flat=True)
    _criar_em_lote(
        por_tag,
        tipo=Notificacao.Tipo.PUBLICACAO,
        titulo="Nova noticia sobre um assunto que voce segue",
        mensagem=noticia.titulo[:300],
        url=url,
    )


def notificar_urgente(noticia):
    from apps.interactions.models import CategoriaSeguida

    ids = CategoriaSeguida.objects.filter(categoria=noticia.categoria).values_list(
        "usuario_id", flat=True)
    _criar_em_lote(
        ids,
        tipo=Notificacao.Tipo.URGENTE,
        titulo="Urgente",
        mensagem=noticia.titulo[:300],
        url=f"/noticia/{noticia.slug}",
    )


def notificar_resposta(comentario):
    pai = comentario.resposta_a
    if not pai or pai.autor_id == comentario.autor_id:
        return
    Notificacao.objects.create(
        usuario=pai.autor,
        tipo=Notificacao.Tipo.RESPOSTA,
        titulo="Seu comentario recebeu uma resposta",
        mensagem=comentario.conteudo[:300],
        url=f"/noticia/{comentario.noticia.slug}",
    )
