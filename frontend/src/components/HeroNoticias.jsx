import { Link } from 'react-router-dom'

import { tempoRelativo } from '../utils/formatar'
import CarrosselNoticias from './CarrosselNoticias'
import CategoriaSelo from './CategoriaSelo'
import { Esqueleto } from './Esqueleto'
import Imagem from './Imagem'

const MAXIMO_SECUNDARIAS = 4

/**
 * Topo da home: carrossel das manchetes (no lugar da antiga imagem grande)
 * e a coluna "Em destaque" ao lado.
 *
 * - `carrossel`: notícias de /api/news/carrossel/ (destaques e mais recentes com imagem).
 * - `principal` e `secundarias`: vindos de /api/news/destaques/, como antes. A coluna
 *   lateral não repete o que já está girando no carrossel.
 * - Se o carrossel vier vazio (nenhuma notícia com imagem), a manchete principal
 *   ocupa o lugar dele, como um slide único.
 */
export default function HeroNoticias({ carrossel = [], principal, secundarias = [], carregando }) {
  const slides = carrossel.length ? carrossel : principal ? [principal] : []

  if (carregando) {
    return (
      <section className="hero" aria-busy="true" aria-label="Carregando manchetes">
        <CarrosselNoticias carregando />
        <div>
          {[0, 1, 2, 3].map((i) => (
            <div key={i} style={{ padding: '14px 0', display: 'grid', gridTemplateColumns: '1fr 96px', gap: 12 }}>
              <div>
                <Esqueleto altura={12} largura="30%" />
                <div style={{ height: 8 }} />
                <Esqueleto altura={18} />
              </div>
              <Esqueleto altura={72} />
            </div>
          ))}
        </div>
      </section>
    )
  }

  if (!slides.length) return null

  const noCarrossel = new Set(slides.map((noticia) => noticia.id))
  const vistos = new Set()
  const lateral = [principal, ...secundarias]
    .filter((noticia) => {
      if (!noticia || noCarrossel.has(noticia.id) || vistos.has(noticia.id)) return false
      vistos.add(noticia.id)
      return true
    })
    .slice(0, MAXIMO_SECUNDARIAS)

  return (
    <section className={`hero${lateral.length ? '' : ' hero--unico'}`} aria-label="Manchetes">
      <h1 className="sr-only">Pauta — principais notícias</h1>
      <CarrosselNoticias noticias={slides} rotulo="Principais notícias" />

      {lateral.length ? (
        <div className="hero__secundarias">
          <div className="hero__rotulo">Em destaque</div>
          {lateral.map((noticia) => (
            <Link key={noticia.id} to={`/noticia/${noticia.slug}`} className="hero__item">
              <div>
                <CategoriaSelo categoria={noticia.categoria} link={false} />
                <h3 style={{ marginTop: 8 }}>{noticia.titulo}</h3>
                <div className="cartao__meta" style={{ marginTop: 6 }}>
                  <time dateTime={noticia.data_publicacao}>{tempoRelativo(noticia.data_publicacao)}</time>
                </div>
              </div>
              <Imagem src={noticia.imagem} largura={104} altura={78} />
            </Link>
          ))}
        </div>
      ) : null}
    </section>
  )
}
