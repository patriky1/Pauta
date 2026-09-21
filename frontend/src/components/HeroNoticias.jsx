import { Link } from 'react-router-dom'

import { tempoRelativo } from '../utils/formatar'
import CategoriaSelo from './CategoriaSelo'
import { Esqueleto } from './Esqueleto'
import Imagem from './Imagem'

export default function HeroNoticias({ principal, secundarias = [], carregando }) {
  if (carregando) {
    return (
      <section className="hero" aria-busy="true" aria-label="Carregando manchetes">
        <div>
          <Esqueleto altura={0} estilo={{ aspectRatio: '16 / 10', borderRadius: 12 }} />
          <div style={{ height: 16 }} />
          <Esqueleto altura={36} />
          <div style={{ height: 8 }} />
          <Esqueleto altura={36} largura="70%" />
        </div>
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

  if (!principal) return null

  return (
    <section className="hero" aria-label="Manchetes">
      <Link to={`/noticia/${principal.slug}`} className="hero__principal">
        <Imagem
          src={principal.imagem}
          alt={principal.imagem_legenda || ''}
          largura={1200}
          altura={750}
          prioridade
        />
        <div style={{ marginTop: 16 }} className="cartao__selos">
          <CategoriaSelo categoria={principal.categoria} link={false} />
          {principal.breaking_news ? <span className="selo selo--exclusivo">Urgente</span> : null}
          {principal.exclusivo ? <span className="selo selo--exclusivo">Exclusivo</span> : null}
        </div>
        <h1 className="hero__titulo">{principal.titulo}</h1>
        {principal.subtitulo ? <p className="hero__linha-fina">{principal.subtitulo}</p> : null}
        <div className="cartao__meta">
          <span>{principal.autor?.nome}</span>
          <span aria-hidden="true">·</span>
          <time dateTime={principal.data_publicacao}>{tempoRelativo(principal.data_publicacao)}</time>
          <span aria-hidden="true">·</span>
          <span>{principal.tempo_leitura || 1} min de leitura</span>
        </div>
      </Link>

      {secundarias.length ? (
        <div className="hero__secundarias">
          <div className="hero__rotulo">Em destaque</div>
          {secundarias.map((noticia) => (
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
