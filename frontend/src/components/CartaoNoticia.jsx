import { Link } from 'react-router-dom'

import { numero, tempoRelativo } from '../utils/formatar'
import CategoriaSelo from './CategoriaSelo'
import Icone from './Icone'
import Imagem from './Imagem'

/**
 * variante: 'vertical' (padrão) | 'horizontal' (lista lateral) | 'texto' (sem imagem)
 */
export default function CartaoNoticia({ noticia, variante = 'vertical', mostrarResumo = true, prioridade = false }) {
  if (!noticia) return null

  return (
    <article className={`cartao cartao--${variante}`}>
      <Link to={`/noticia/${noticia.slug}`} className="cartao__link">
        {variante !== 'texto' ? (
          <Imagem
            src={noticia.imagem}
            alt={noticia.imagem_legenda || ''}
            largura={640}
            altura={400}
            prioridade={prioridade}
          />
        ) : null}

        <div className="cartao__corpo">
          <div className="cartao__selos">
            <CategoriaSelo categoria={noticia.categoria} link={false} />
            {noticia.exclusivo ? <span className="selo selo--exclusivo">Exclusivo</span> : null}
            {noticia.breaking_news ? <span className="selo selo--exclusivo">Urgente</span> : null}
          </div>

          <h3 className="cartao__titulo">{noticia.titulo}</h3>

          {mostrarResumo && variante === 'vertical' && noticia.resumo ? (
            <p className="cartao__resumo">{noticia.resumo}</p>
          ) : null}

          <div className="cartao__meta">
            {variante === 'vertical' && noticia.autor?.nome ? (
              <>
                <span>{noticia.autor.nome}</span>
                <span aria-hidden="true">·</span>
              </>
            ) : null}
            <time dateTime={noticia.data_publicacao}>{tempoRelativo(noticia.data_publicacao)}</time>
            <span aria-hidden="true">·</span>
            <span title={`${noticia.visualizacoes || 0} leituras`}>
              <Icone nome="olho" tamanho={13} /> {numero(noticia.visualizacoes)}
            </span>
          </div>
        </div>
      </Link>
    </article>
  )
}
