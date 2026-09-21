import { useState } from 'react'

import { useAuth } from '../contexts/AuthContext'
import { useAviso } from '../contexts/AvisoContext'
import { social } from '../services/social'
import { iniciais, tempoRelativo } from '../utils/formatar'
import Icone from './Icone'

export default function Comentario({ comentario, aoResponder, aoAtualizar, aoRemover, nivel = 0 }) {
  const { usuario, ehAdmin } = useAuth()
  const { mostrar } = useAviso()
  const [editando, setEditando] = useState(false)
  const [texto, setTexto] = useState(comentario.conteudo)
  const [curtido, setCurtido] = useState(Boolean(comentario.curtido))
  const [curtidas, setCurtidas] = useState(comentario.total_curtidas || 0)
  const [respondendo, setRespondendo] = useState(false)
  const [resposta, setResposta] = useState('')
  const [denunciado, setDenunciado] = useState(false)

  const meu = usuario && comentario.autor?.id === usuario.id
  const removido = comentario.status === 'REMOVIDO'

  const curtir = async () => {
    if (!usuario) { mostrar('Entre na sua conta para curtir.', 'erro'); return }
    try {
      const dados = await social.curtirComentario(comentario.id)
      setCurtido(dados.curtido)
      setCurtidas(dados.total_curtidas)
    } catch {
      mostrar('Não foi possível curtir agora.', 'erro')
    }
  }

  const salvarEdicao = async () => {
    if (texto.trim().length < 3) return
    try {
      const atualizado = await social.editarComentario(comentario.id, texto.trim())
      setEditando(false)
      aoAtualizar?.(atualizado)
    } catch {
      mostrar('Não foi possível salvar a edição.', 'erro')
    }
  }

  const enviarResposta = async (evento) => {
    evento.preventDefault()
    if (resposta.trim().length < 2) return
    await aoResponder?.(resposta.trim(), comentario.id)
    setResposta('')
    setRespondendo(false)
  }

  const denunciar = async () => {
    try {
      await social.denunciar({ comentario: comentario.id, motivo: 'OUTRO' })
      setDenunciado(true)
      mostrar('Denúncia enviada para a moderação.')
    } catch {
      mostrar('Você já denunciou este comentário.', 'erro')
    }
  }

  return (
    <article className="comentario">
      <div className="comentario__cabecalho">
        {comentario.autor?.foto ? (
          <img className="avatar avatar--p" src={comentario.autor.foto} alt="" />
        ) : (
          <span className="avatar avatar--p" aria-hidden="true">{iniciais(comentario.autor?.nome || '?')}</span>
        )}
        <span className="comentario__nome">{comentario.autor?.nome}</span>
        <time className="comentario__data" dateTime={comentario.criado_em}>
          {tempoRelativo(comentario.criado_em)}
        </time>
        {comentario.editado ? <span className="comentario__data">· editado</span> : null}
      </div>

      {editando ? (
        <div className="campo" style={{ marginTop: 10, marginBottom: 0 }}>
          <label className="sr-only" htmlFor={`editar-${comentario.id}`}>Editar comentário</label>
          <textarea id={`editar-${comentario.id}`} value={texto} onChange={(evento) => setTexto(evento.target.value)} />
          <div className="grupo-botoes">
            <button type="button" className="botao botao--primario botao--pequeno" onClick={salvarEdicao}>Salvar</button>
            <button type="button" className="botao botao--pequeno" onClick={() => { setEditando(false); setTexto(comentario.conteudo) }}>
              Cancelar
            </button>
          </div>
        </div>
      ) : (
        <p className="comentario__texto" style={{ opacity: removido ? 0.6 : 1, fontStyle: removido ? 'italic' : 'normal' }}>
          {comentario.conteudo}
        </p>
      )}

      {!removido && !editando ? (
        <div className="comentario__acoes">
          <button type="button" onClick={curtir} aria-pressed={curtido} aria-label={`Curtir (${curtidas})`}>
            <Icone nome="coracao" tamanho={13} preenchido={curtido} /> {curtidas}
          </button>
          {nivel === 0 && usuario ? (
            <button type="button" onClick={() => setRespondendo((v) => !v)}>
              <Icone nome="comentario" tamanho={13} preenchido={false} /> Responder
            </button>
          ) : null}
          {meu ? <button type="button" onClick={() => setEditando(true)}>Editar</button> : null}
          {meu || ehAdmin ? (
            <button type="button" onClick={() => aoRemover?.(comentario)}>Excluir</button>
          ) : null}
          {!meu && usuario ? (
            <button type="button" onClick={denunciar} disabled={denunciado}>
              {denunciado ? 'Denunciado' : 'Denunciar'}
            </button>
          ) : null}
        </div>
      ) : null}

      {respondendo ? (
        <form onSubmit={enviarResposta} className="campo" style={{ marginTop: 10, marginBottom: 0 }}>
          <label className="sr-only" htmlFor={`responder-${comentario.id}`}>Sua resposta</label>
          <textarea
            id={`responder-${comentario.id}`}
            value={resposta}
            onChange={(evento) => setResposta(evento.target.value)}
            placeholder={`Responder a ${comentario.autor?.nome}`}
            style={{ minHeight: 80 }}
            autoFocus
          />
          <div className="grupo-botoes">
            <button type="submit" className="botao botao--primario botao--pequeno" disabled={resposta.trim().length < 2}>
              Publicar resposta
            </button>
            <button type="button" className="botao botao--pequeno" onClick={() => setRespondendo(false)}>Cancelar</button>
          </div>
        </form>
      ) : null}

      {comentario.respostas?.length ? (
        <div className="comentario__respostas">
          {comentario.respostas.map((filho) => (
            <Comentario
              key={filho.id}
              comentario={filho}
              nivel={nivel + 1}
              aoAtualizar={aoAtualizar}
              aoRemover={aoRemover}
            />
          ))}
        </div>
      ) : null}
    </article>
  )
}
