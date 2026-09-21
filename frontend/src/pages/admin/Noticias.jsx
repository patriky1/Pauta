import { useCallback, useState } from 'react'
import { Link } from 'react-router-dom'

import { Esqueleto } from '../../components/Esqueleto'
import { EstadoErro, EstadoVazio } from '../../components/Estado'
import { useAviso } from '../../contexts/AvisoContext'
import useRequisicao from '../../hooks/useRequisicao'
import useSeo from '../../hooks/useSeo'
import { painel } from '../../services/painel'
import { dataCurta, numero } from '../../utils/formatar'
import { STATUS_NOTICIA } from '../../utils/constantes'

export default function NoticiasAdmin() {
  const [status, setStatus] = useState('')
  const [busca, setBusca] = useState('')
  const { mostrar } = useAviso()
  useSeo({ titulo: 'Notícias — painel' })

  const buscar = useCallback(
    () => painel.noticias({ status: status || undefined, search: busca || undefined, page_size: 24 }),
    [status, busca]
  )
  const { dados, carregando, erro, recarregar } = useRequisicao(buscar, [status, busca])

  const acao = async (funcao, slug, mensagem) => {
    try {
      await funcao(slug)
      mostrar(mensagem)
      recarregar()
    } catch (falha) {
      mostrar(falha.mensagem || 'Não foi possível concluir.', 'erro')
    }
  }

  const excluir = async (noticia) => {
    if (!window.confirm(`Excluir “${noticia.titulo}”? Essa ação não tem volta.`)) return
    await acao(painel.excluirNoticia, noticia.slug, 'Notícia excluída.')
  }

  const lista = dados?.results || []

  return (
    <div>
      <div className="pagina__cabecalho">
        <div>
          <h1 className="titulo-pagina">Notícias</h1>
          <p className="pagina__descricao">{dados?.count ?? 0} matérias no total.</p>
        </div>
        <Link to="/admin/noticias/nova" className="botao botao--primario">Nova notícia</Link>
      </div>

      <div className="filtros" style={{ marginBottom: 'var(--e-2)' }}>
        <div className="campo">
          <label htmlFor="filtro-status">Status</label>
          <select id="filtro-status" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Todos</option>
            {STATUS_NOTICIA.map((item) => (
              <option key={item.valor} value={item.valor}>{item.rotulo}</option>
            ))}
          </select>
        </div>
        <div className="campo">
          <label htmlFor="filtro-busca">Buscar</label>
          <input id="filtro-busca" value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Título ou resumo" />
        </div>
      </div>

      {erro ? <EstadoErro mensagem={erro} aoTentarNovamente={recarregar} /> : null}
      {carregando ? <Esqueleto altura={220} /> : null}
      {!carregando && !lista.length ? (
        <EstadoVazio titulo="Nenhuma notícia com esses filtros" />
      ) : null}

      {lista.length ? (
        <div className="tabela-rolagem">
        <table className="tabela">
          <thead>
            <tr>
              <th>Título</th><th>Status</th><th>Categoria</th><th>Publicação</th><th>Leituras</th><th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {lista.map((noticia) => (
              <tr key={noticia.id}>
                <td>
                  <Link to={`/admin/noticias/${noticia.slug}/editar`}>{noticia.titulo}</Link>
                  {noticia.destaque ? <span className="etiqueta etiqueta--revisao" style={{ marginLeft: 6 }}>destaque</span> : null}
                  {noticia.breaking_news ? <span className="etiqueta etiqueta--arquivada" style={{ marginLeft: 6 }}>urgente</span> : null}
                </td>
                <td><span className={`etiqueta etiqueta--${String(noticia.status).toLowerCase()}`}>{STATUS_NOTICIA.find((i) => i.valor === noticia.status)?.rotulo || noticia.status}</span></td>
                <td>{noticia.categoria?.nome}</td>
                <td>{noticia.data_publicacao ? dataCurta(noticia.data_publicacao) : '—'}</td>
                <td>{numero(noticia.visualizacoes)}</td>
                <td><div className="grupo-botoes" style={{ flexWrap: 'nowrap' }}>
                  {noticia.status !== 'PUBLICADA' ? (
                    <button type="button" className="botao botao--pequeno" onClick={() => acao(painel.publicar, noticia.slug, 'Publicada.')}>
                      Publicar
                    </button>
                  ) : (
                    <button type="button" className="botao botao--pequeno" onClick={() => acao(painel.arquivar, noticia.slug, 'Arquivada.')}>
                      Arquivar
                    </button>
                  )}
                  <button type="button" className="botao botao--pequeno" onClick={() => acao(painel.destacar, noticia.slug, 'Destaque alterado.')}>
                    Destacar
                  </button>
                  <button type="button" className="botao botao--pequeno" onClick={() => acao(painel.marcarUrgente, noticia.slug, 'Urgência alterada.')}>
                    Urgente
                  </button>
                  <button type="button" className="botao botao--pequeno botao--contorno-perigo" onClick={() => excluir(noticia)}>
                    Excluir
                  </button>
                </div></td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      ) : null}
    </div>
  )
}
