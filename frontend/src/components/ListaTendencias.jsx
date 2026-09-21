import { Link } from 'react-router-dom'

import { numero } from '../utils/formatar'

export default function ListaTendencias({ assuntos = [], titulo = 'Tendências', limite = 6 }) {
  if (!assuntos.length) return null
  return (
    <section aria-label={titulo}>
      <div className="secao__cabecalho">
        <h2 className="secao__titulo" style={{ fontSize: 'var(--t-xl)' }}>{titulo}</h2>
        <Link className="secao__link" to="/tendencias">Ver todas</Link>
      </div>
      <ol className="tendencias">
        {assuntos.slice(0, limite).map((assunto, posicao) => (
          <li key={assunto.slug} className="tendencias__item">
            <span className="tendencias__posicao">{posicao + 1}</span>
            <Link to={assunto.cor ? `/categoria/${assunto.slug}` : `/busca?tag=${assunto.slug}`}>
              {assunto.nome}
            </Link>
            <span className="tendencias__total">{numero(assunto.total)} leituras</span>
          </li>
        ))}
      </ol>
    </section>
  )
}
