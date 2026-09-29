import { Link } from 'react-router-dom'

import GradeNoticias from '../components/GradeNoticias'
import useRequisicao from '../hooks/useRequisicao'
import useSeo from '../hooks/useSeo'
import { noticias as servico } from '../services/noticias'
import { numero } from '../utils/formatar'

export default function Tendencias() {
  const { dados, carregando, erro, recarregar } = useRequisicao(() => servico.tendencias(), [])
  useSeo({ titulo: 'Tendências', descricao: 'Os assuntos mais lidos agora no Pauta.', caminho: '/tendencias' })

  const assuntos = dados?.assuntos || []

  return (
    <div className="container pagina">
      <header className="pagina__cabecalho">
        <div>
          <h1 className="titulo-pagina">Tendências</h1>
          <p className="pagina__descricao">Ranking calculado a partir das leituras das últimas 48 horas.</p>
        </div>
      </header>

      <div className="coluna-dupla">
        <div style={{ minWidth: 0 }}>
          <GradeNoticias
            noticias={dados?.noticias || []}
            carregando={carregando}
            erro={erro}
            aoRecarregar={recarregar}
            vazioTitulo="Ainda sem dados suficientes"
            vazioDescricao="O ranking aparece assim que as primeiras leituras forem registradas."
          />
        </div>

        <aside className="lateral">
          {assuntos.length ? (
            <section className="bloco">
              <h2 className="secao__titulo secao__titulo--pequeno" style={{ marginBottom: 'var(--e-2)' }}>
                Editorias em alta
              </h2>
              <ol className="tendencias">
                {assuntos.map((assunto, posicao) => (
                  <li key={assunto.slug} className="tendencias__item">
                    <span className="tendencias__posicao">{posicao + 1}</span>
                    <Link to={`/categoria/${assunto.slug}`}>{assunto.nome}</Link>
                    <span className="tendencias__total">{numero(assunto.total)} leituras</span>
                  </li>
                ))}
              </ol>
            </section>
          ) : null}
          {dados?.tags?.length ? (
            <section className="bloco">
              <h2 className="secao__titulo secao__titulo--pequeno" style={{ marginBottom: 'var(--e-3)' }}>
                Assuntos em alta
              </h2>
              <div className="grupo-botoes">
                {dados.tags.map((tag) => (
                  <Link key={tag.slug} to={`/busca?tag=${tag.slug}`} className="selo selo--linha">#{tag.nome}</Link>
                ))}
              </div>
            </section>
          ) : null}
        </aside>
      </div>
    </div>
  )
}
