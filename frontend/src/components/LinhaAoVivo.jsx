import { hora } from '../utils/formatar'

export default function LinhaAoVivo({ atualizacoes = [] }) {
  if (!atualizacoes.length) {
    return <p style={{ color: 'var(--grafite)' }}>A cobertura começa em instantes.</p>
  }
  return (
    <ol className="ao-vivo">
      {atualizacoes.map((item) => (
        <li key={item.id} className={`ao-vivo__item${item.importante ? ' ao-vivo__item--destaque' : ''}`}>
          <time className="ao-vivo__hora" dateTime={item.horario}>{hora(item.horario)}</time>
          {item.titulo ? <h3 style={{ fontSize: 'var(--t-lg)', margin: '4px 0' }}>{item.titulo}</h3> : null}
          <p style={{ margin: 0 }}>{item.conteudo}</p>
          {item.autor ? (
            <span style={{ fontSize: 'var(--t-xs)', color: 'var(--grafite)' }}>{item.autor.nome}</span>
          ) : null}
        </li>
      ))}
    </ol>
  )
}
