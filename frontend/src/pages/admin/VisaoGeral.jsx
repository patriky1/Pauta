import { Link } from 'react-router-dom'

import { Esqueleto } from '../../components/Esqueleto'
import { EstadoErro } from '../../components/Estado'
import useRequisicao from '../../hooks/useRequisicao'
import useSeo from '../../hooks/useSeo'
import { painel } from '../../services/painel'
import { dataCurta, numero } from '../../utils/formatar'

const INDICADORES = [
  ['publicadas', 'Notícias publicadas'],
  ['rascunhos', 'Rascunhos'],
  ['visualizacoes', 'Leituras acumuladas'],
  ['usuarios', 'Usuários'],
  ['comentarios', 'Comentários'],
  ['denuncias_abertas', 'Denúncias abertas'],
]

export default function VisaoGeral() {
  const { dados, carregando, erro, recarregar } = useRequisicao(() => painel.resumo(), [])
  useSeo({ titulo: 'Painel' })

  if (erro) return <EstadoErro mensagem={erro} aoTentarNovamente={recarregar} />
  if (carregando) {
    return (
      <div style={{ display: 'grid', gap: 12 }}>
        <Esqueleto altura={28} largura="30%" />
        <Esqueleto altura={90} />
        <Esqueleto altura={200} />
      </div>
    )
  }

  const serie = dados?.serie || []
  const totais = dados?.totais || {}
  const maximo = Math.max(1, ...serie.map((ponto) => ponto.visualizacoes))

  return (
    <div>
      <div className="pagina__cabecalho">
        <div>
          <h1 className="titulo-pagina">Visão geral</h1>
          <p className="pagina__descricao">Desempenho da redação e da audiência.</p>
        </div>
        <Link to="/admin/noticias/nova" className="botao botao--primario">Nova notícia</Link>
      </div>

      <div className="indicadores">
        {INDICADORES.map(([chave, rotulo]) => (
          <div key={chave} className={`indicador${chave === 'denuncias_abertas' && totais[chave] > 0 ? ' indicador--alerta' : ''}`}>
            <div className="indicador__valor">{numero(totais[chave])}</div>
            <div className="indicador__rotulo">{rotulo}</div>
          </div>
        ))}
      </div>

      <section className="bloco" style={{ marginTop: 'var(--e-4)' }}>
        <h2 className="secao__titulo secao__titulo--pequeno">Leituras nos últimos 14 dias</h2>
        {serie.length ? (
          <>
            <div className="grafico" role="img" aria-label="Gráfico de leituras por dia">
              {serie.map((ponto) => (
                <div
                  key={ponto.dia}
                  className="grafico__barra"
                  style={{ height: `${(ponto.visualizacoes / maximo) * 100}%` }}
                  title={`${dataCurta(ponto.dia)}: ${ponto.visualizacoes} leituras`}
                />
              ))}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--t-xs)', color: 'var(--grafite)' }}>
              <span>{dataCurta(serie[0]?.dia)}</span>
              <span>{dataCurta(serie[serie.length - 1]?.dia)}</span>
            </div>
          </>
        ) : (
          <p style={{ color: 'var(--grafite)' }}>Sem leituras registradas no período.</p>
        )}
      </section>

      <section style={{ marginTop: 'var(--e-5)' }}>
        <h2 className="secao__titulo secao__titulo--pequeno" style={{ marginBottom: 'var(--e-3)' }}>Matérias mais lidas</h2>
        <div className="tabela-rolagem">
        <table className="tabela">
          <thead>
            <tr><th>Título</th><th>Categoria</th><th>Leituras</th></tr>
          </thead>
          <tbody>
            {(dados.top_noticias || []).map((noticia) => (
              <tr key={noticia.id}>
                <td><Link to={`/noticia/${noticia.slug}`}>{noticia.titulo}</Link></td>
                <td><span className="etiqueta">{noticia.categoria?.nome}</span></td>
                <td>{numero(noticia.visualizacoes)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </section>
    </div>
  )
}
