import { useCallback, useState } from 'react'

import AbasFeed from '../../components/AbasFeed'
import { Esqueleto } from '../../components/Esqueleto'
import { EstadoErro, EstadoVazio } from '../../components/Estado'
import { useAviso } from '../../contexts/AvisoContext'
import useRequisicao from '../../hooks/useRequisicao'
import useSeo from '../../hooks/useSeo'
import { painel } from '../../services/painel'
import { tempoRelativo } from '../../utils/formatar'

const ABAS = [
  { chave: 'pendentes', rotulo: 'Comentários recentes' },
  { chave: 'denuncias', rotulo: 'Denúncias' },
]

export default function Moderacao() {
  const [aba, setAba] = useState('pendentes')
  const { mostrar } = useAviso()
  useSeo({ titulo: 'Moderação — painel' })

  const buscar = useCallback(
    () =>
      aba === 'pendentes'
        ? painel.comentariosPendentes({ page_size: 30 })
        : painel.denuncias({ status: 'ABERTA' }),
    [aba]
  )
  const { dados, carregando, erro, recarregar } = useRequisicao(buscar, [aba])

  const agir = async (promessa, mensagem) => {
    await promessa
    mostrar(mensagem)
    recarregar()
  }

  const itens = dados?.results || []

  return (
    <div>
      <div className="pagina__cabecalho">
        <div>
          <h1 className="titulo-pagina">Moderação</h1>
          <p className="pagina__descricao">Revise comentários e denúncias da comunidade.</p>
        </div>
      </div>
      <AbasFeed abas={ABAS} ativa={aba} aoTrocar={setAba} />

      {erro ? <EstadoErro mensagem={erro} aoTentarNovamente={recarregar} /> : null}
      {carregando ? <Esqueleto altura={180} /> : null}
      {!carregando && !itens.length ? (
        <EstadoVazio titulo="Fila vazia" descricao="Nada aguardando moderação no momento." />
      ) : null}

      <div style={{ display: 'grid', gap: 'var(--e-3)' }}>
        {itens.map((item) => (
          <article key={item.id} className="bloco">
            <p style={{ marginBottom: 6 }} className="comentario__texto">
              {aba === 'pendentes' ? item.conteudo : item.comentario_conteudo}
            </p>
            <div className="cartao__meta">
              <span>{aba === 'pendentes' ? item.autor?.nome : item.usuario?.nome}</span>
              <span aria-hidden="true">·</span>
              <time>{tempoRelativo(item.criado_em)}</time>
              {aba === 'denuncias' ? <span className="etiqueta">{item.motivo}</span> : null}
              {aba === 'pendentes' ? <span className={`etiqueta etiqueta--${String(item.status).toLowerCase() === 'publicado' ? 'publicada' : String(item.status).toLowerCase()}`}>{item.status}</span> : null}
            </div>
            <div className="grupo-botoes" style={{ marginTop: 10 }}>
              <button
                type="button"
                className="botao botao--pequeno"
                onClick={() =>
                  agir(painel.aprovarComentario(aba === 'pendentes' ? item.id : item.comentario), 'Comentário liberado.')
                }
              >
                Aprovar
              </button>
              <button
                type="button"
                className="botao botao--pequeno botao--contorno-perigo"
                onClick={() =>
                  agir(painel.ocultarComentario(aba === 'pendentes' ? item.id : item.comentario), 'Comentário ocultado.')
                }
              >
                Ocultar
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
