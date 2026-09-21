import { Link } from 'react-router-dom'

import { iniciais, numero } from '../utils/formatar'

export default function CartaoAutor({ autor, aoSeguir, compacto = false }) {
  if (!autor) return null
  const classeAvatar = compacto ? 'avatar' : 'avatar avatar--g'

  return (
    <div style={{ display: 'flex', gap: 'var(--e-3)', alignItems: 'center', minWidth: 0 }}>
      {autor.foto ? (
        <img className={classeAvatar} src={autor.foto} alt="" />
      ) : (
        <span className={classeAvatar} aria-hidden="true">{iniciais(autor.nome)}</span>
      )}
      <div style={{ flex: 1, minWidth: 0 }}>
        <Link to={`/autor/${autor.username}`} style={{ fontWeight: 600 }}>
          {autor.nome}
        </Link>
        {!compacto && autor.biografia ? (
          <p className="cartao__resumo" style={{ marginTop: 4 }}>{autor.biografia}</p>
        ) : null}
        {autor.total_noticias ? (
          <div className="cartao__meta">
            <span>{numero(autor.total_noticias)} publicações</span>
            {autor.total_visualizacoes ? (
              <>
                <span aria-hidden="true">·</span>
                <span>{numero(autor.total_visualizacoes)} leituras</span>
              </>
            ) : null}
          </div>
        ) : null}
      </div>
      {aoSeguir ? (
        <button
          type="button"
          className={`botao${autor.seguindo ? '' : ' botao--primario'}`}
          onClick={() => aoSeguir(autor)}
        >
          {autor.seguindo ? 'Seguindo' : 'Seguir'}
        </button>
      ) : null}
    </div>
  )
}
