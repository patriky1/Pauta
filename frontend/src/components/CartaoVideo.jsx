import { duracao, numero } from '../utils/formatar'
import CategoriaSelo from './CategoriaSelo'
import Icone from './Icone'
import Imagem from './Imagem'

export default function CartaoVideo({ video, aoAbrir }) {
  return (
    <article className="cartao">
      <button
        type="button"
        className="cartao__link"
        onClick={() => aoAbrir?.(video)}
        style={{ border: 0, background: 'transparent', padding: 0, textAlign: 'left', width: '100%' }}
        aria-label={`Assistir: ${video.titulo}`}
      >
        <div style={{ position: 'relative' }}>
          <Imagem src={video.capa} estilo={{ aspectRatio: '16 / 9' }} />
          <span
            className="selo"
            style={{ position: 'absolute', right: 8, bottom: 8, background: 'rgba(11,15,24,.82)', color: '#fff' }}
          >
            <Icone nome="video" tamanho={12} /> {duracao(video.duracao_segundos)}
          </span>
        </div>
        <div className="cartao__corpo">
          <div className="cartao__selos"><CategoriaSelo categoria={video.categoria} link={false} /></div>
          <h3 className="cartao__titulo">{video.titulo}</h3>
          <div className="cartao__meta">
            <span>{numero(video.visualizacoes)} visualizações</span>
          </div>
        </div>
      </button>
    </article>
  )
}
