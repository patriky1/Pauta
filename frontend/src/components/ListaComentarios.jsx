import { useCallback, useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext'
import { useAviso } from '../contexts/AvisoContext'
import useRequisicao from '../hooks/useRequisicao'
import { social } from '../services/social'
import Comentario from './Comentario'
import { Esqueleto } from './Esqueleto'
import { EstadoErro } from './Estado'

export default function ListaComentarios({ noticia }) {
  const { usuario } = useAuth()
  const { mostrar } = useAviso()
  const [texto, setTexto] = useState('')
  const [enviando, setEnviando] = useState(false)

  const buscar = useCallback(() => social.comentarios(noticia.id), [noticia.id])
  const { dados, carregando, erro, recarregar, setDados } = useRequisicao(buscar, [noticia.id])

  const comentarios = dados?.results || []

  const publicar = async (conteudo, respostaA = null) => {
    try {
      await social.comentar({ noticia: noticia.id, conteudo, resposta_a: respostaA })
      setTexto('')
      recarregar()
      mostrar('Comentário publicado.')
    } catch (falha) {
      mostrar(falha.mensagem || 'Não foi possível comentar.', 'erro')
    }
  }

  const enviar = async (evento) => {
    evento.preventDefault()
    if (texto.trim().length < 3) return
    setEnviando(true)
    await publicar(texto.trim())
    setEnviando(false)
  }

  const remover = async (comentario) => {
    await social.excluirComentario(comentario.id)
    setDados((atual) => ({
      ...atual,
      results: (atual?.results || []).filter((item) => item.id !== comentario.id),
    }))
    mostrar('Comentário removido.')
  }

  if (!noticia.permitir_comentarios) {
    return (
      <section className="comentarios">
        <h2 className="secao__titulo">Comentários</h2>
        <p style={{ color: 'var(--grafite)' }}>Os comentários estão desativados nesta matéria.</p>
      </section>
    )
  }

  return (
    <section className="comentarios" id="comentarios">
      <div className="secao__cabecalho">
        <h2 className="secao__titulo">
          Comentários{dados?.count ? ` (${dados.count})` : ''}
        </h2>
      </div>

      {usuario ? (
        <form onSubmit={enviar} className="campo">
          <label htmlFor="novo-comentario" className="sr-only">Escreva um comentário</label>
          <textarea
            id="novo-comentario"
            value={texto}
            onChange={(evento) => setTexto(evento.target.value)}
            placeholder="O que você achou desta matéria?"
            maxLength={2000}
          />
          <button type="submit" className="botao botao--primario" disabled={enviando || texto.trim().length < 3}>
            {enviando ? 'Publicando…' : 'Publicar comentário'}
          </button>
        </form>
      ) : (
        <p style={{ color: 'var(--grafite)' }}>
          <Link to="/entrar">Entre na sua conta</Link> para comentar.
        </p>
      )}

      {erro ? <EstadoErro mensagem={erro} aoTentarNovamente={recarregar} /> : null}
      {carregando ? (
        <div style={{ display: 'grid', gap: 12, marginTop: 16 }}>
          <Esqueleto altura={54} />
          <Esqueleto altura={54} />
        </div>
      ) : null}

      {!carregando && comentarios.length === 0 ? (
        <p style={{ color: 'var(--grafite)' }}>Ninguém comentou ainda. Comece a conversa.</p>
      ) : null}

      {comentarios.map((comentario) => (
        <Comentario
          key={comentario.id}
          comentario={comentario}
          aoResponder={publicar}
          aoAtualizar={recarregar}
          aoRemover={remover}
        />
      ))}
    </section>
  )
}
