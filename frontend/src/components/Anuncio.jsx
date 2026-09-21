import { useEffect, useState } from 'react'

import api from '../services/api'
import { catalogo } from '../services/noticias'

export default function Anuncio({ posicao = 'LATERAL' }) {
  const [anuncio, setAnuncio] = useState(null)

  useEffect(() => {
    let ativo = true
    catalogo
      .anuncios(posicao)
      .then((dados) => {
        const lista = dados.results || dados
        if (ativo && lista?.length) setAnuncio(lista[Math.floor(Math.random() * lista.length)])
      })
      .catch(() => null)
    return () => { ativo = false }
  }, [posicao])

  if (!anuncio) return null

  return (
    <aside className="anuncio">
      <div className="anuncio__rotulo">Publicidade</div>
      <a
        href={anuncio.url_destino}
        target="_blank"
        rel="noopener noreferrer sponsored"
        onClick={() => api.post(`/ads/${anuncio.id}/clique/`).catch(() => null)}
      >
        {anuncio.imagem_final ? (
          <img src={anuncio.imagem_final} alt={anuncio.titulo} loading="lazy" />
        ) : (
          <div style={{ padding: 'var(--e-4)' }}>{anuncio.titulo}</div>
        )}
      </a>
    </aside>
  )
}
