import { useCallback, useState } from 'react'

import LinhaAoVivo from '../../components/LinhaAoVivo'
import { Esqueleto } from '../../components/Esqueleto'
import { EstadoErro, EstadoVazio } from '../../components/Estado'
import { useAviso } from '../../contexts/AvisoContext'
import useRequisicao from '../../hooks/useRequisicao'
import useSeo from '../../hooks/useSeo'
import { catalogo } from '../../services/noticias'
import { painel } from '../../services/painel'

export default function AoVivoAdmin() {
  const { mostrar } = useAviso()
  const [selecionada, setSelecionada] = useState(null)
  const [nova, setNova] = useState({ titulo: '', resumo: '', categoria_id: '' })
  const [atualizacao, setAtualizacao] = useState({ titulo: '', conteudo: '', importante: false })

  useSeo({ titulo: 'Ao vivo — painel' })
  const { dados: categorias } = useRequisicao(() => catalogo.categorias(), [])
  const buscar = useCallback(() => painel.coberturas(), [])
  const { dados, carregando, erro, recarregar } = useRequisicao(buscar, [])

  const coberturas = dados?.results || []

  const criar = async (evento) => {
    evento.preventDefault()
    try {
      await painel.criarCobertura({ ...nova, categoria_id: Number(nova.categoria_id) })
      setNova({ titulo: '', resumo: '', categoria_id: '' })
      mostrar('Cobertura criada.')
      recarregar()
    } catch (falha) {
      mostrar(falha.mensagem || 'Não foi possível criar.', 'erro')
    }
  }

  const publicarAtualizacao = async (evento) => {
    evento.preventDefault()
    const atualizada = await painel.adicionarAtualizacao(selecionada.slug, atualizacao)
    setSelecionada({
      ...selecionada,
      atualizacoes: [atualizada, ...(selecionada.atualizacoes || [])],
    })
    setAtualizacao({ titulo: '', conteudo: '', importante: false })
    mostrar('Atualização publicada.')
  }

  const abrir = async (cobertura) => {
    const completa = await catalogo.cobertura(cobertura.slug)
    setSelecionada(completa)
  }

  if (erro) return <EstadoErro mensagem={erro} aoTentarNovamente={recarregar} />

  return (
    <div>
      <div className="pagina__cabecalho">
        <div>
          <h1 className="titulo-pagina">Coberturas ao vivo</h1>
          <p className="pagina__descricao">Crie coberturas e publique atualizações minuto a minuto.</p>
        </div>
      </div>

      <div className="coluna-dupla">
        <div>
          {carregando ? <Esqueleto altura={140} /> : null}
          {!carregando && !coberturas.length ? (
            <EstadoVazio titulo="Nenhuma cobertura criada" descricao="Crie uma ao lado para começar." />
          ) : null}

          <div style={{ display: 'grid', gap: 'var(--e-3)' }}>
            {coberturas.map((cobertura) => (
              <article key={cobertura.id} className="bloco">
                <h2 style={{ fontSize: 'var(--t-lg)' }}>{cobertura.titulo}</h2>
                <span className={`etiqueta etiqueta--${cobertura.status === 'AO_VIVO' ? 'publicada' : 'rascunho'}`}>{cobertura.status === 'AO_VIVO' ? 'No ar' : 'Encerrada'}</span>
                <div className="grupo-botoes" style={{ marginTop: 10 }}>
                  <button type="button" className="botao" onClick={() => abrir(cobertura)}>
                    Abrir
                  </button>
                  {cobertura.status === 'AO_VIVO' ? (
                    <button
                      type="button"
                      className="botao botao--perigo"
                      onClick={async () => {
                        await painel.encerrarCobertura(cobertura.slug)
                        mostrar('Cobertura encerrada.')
                        recarregar()
                      }}
                    >
                      Encerrar
                    </button>
                  ) : null}
                </div>
              </article>
            ))}
          </div>

          {selecionada ? (
            <section className="bloco" style={{ marginTop: 'var(--e-4)' }}>
              <h2 style={{ fontSize: 'var(--t-xl)' }}>{selecionada.titulo}</h2>
              <form onSubmit={publicarAtualizacao} style={{ margin: 'var(--e-3) 0' }}>
                <div className="campo">
                  <label htmlFor="at-titulo">Título da atualização</label>
                  <input
                    id="at-titulo"
                    value={atualizacao.titulo}
                    onChange={(e) => setAtualizacao({ ...atualizacao, titulo: e.target.value })}
                  />
                </div>
                <div className="campo">
                  <label htmlFor="at-conteudo">O que aconteceu</label>
                  <textarea
                    id="at-conteudo"
                    value={atualizacao.conteudo}
                    onChange={(e) => setAtualizacao({ ...atualizacao, conteudo: e.target.value })}
                    required
                  />
                </div>
                <label className="caixa-selecao">
                  <input
                    type="checkbox"
                    checked={atualizacao.importante}
                    onChange={(e) => setAtualizacao({ ...atualizacao, importante: e.target.checked })}
                  />
                  Destacar esta atualização
                </label>
                <button type="submit" className="botao botao--primario" style={{ marginTop: 10 }}>
                  Publicar atualização
                </button>
              </form>
              <LinhaAoVivo atualizacoes={selecionada.atualizacoes} />
            </section>
          ) : null}
        </div>

        <aside className="lateral">
          <form onSubmit={criar} className="bloco">
            <h2 style={{ fontSize: 'var(--t-xl)', marginBottom: 'var(--e-3)' }}>Nova cobertura</h2>
            <div className="campo">
              <label htmlFor="nova-titulo">Título</label>
              <input id="nova-titulo" value={nova.titulo} onChange={(e) => setNova({ ...nova, titulo: e.target.value })} required />
            </div>
            <div className="campo">
              <label htmlFor="nova-resumo">Resumo</label>
              <textarea id="nova-resumo" value={nova.resumo} onChange={(e) => setNova({ ...nova, resumo: e.target.value })} />
            </div>
            <div className="campo">
              <label htmlFor="nova-categoria">Categoria</label>
              <select
                id="nova-categoria"
                value={nova.categoria_id}
                onChange={(e) => setNova({ ...nova, categoria_id: e.target.value })}
                required
              >
                <option value="">Selecione</option>
                {(categorias || []).map((categoria) => (
                  <option key={categoria.id} value={categoria.id}>{categoria.nome}</option>
                ))}
              </select>
            </div>
            <button type="submit" className="botao botao--primario botao--bloco">Criar cobertura</button>
          </form>
        </aside>
      </div>
    </div>
  )
}
