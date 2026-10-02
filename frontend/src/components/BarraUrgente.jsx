import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import useIntervalo from '../hooks/useIntervalo'
import useRequisicao from '../hooks/useRequisicao'
import { noticias as servicoNoticias } from '../services/noticias'

export default function BarraUrgente() {
  const { dados, recarregar } = useRequisicao(() => servicoNoticias.urgentes(), [])
  const [indice, setIndice] = useState(0)
  const itens = dados || []

  useEffect(() => {
    if (itens.length < 2) return undefined
    const id = setInterval(() => setIndice((atual) => (atual + 1) % itens.length), 6000)
    return () => clearInterval(id)
  }, [itens.length])

  // a coleta roda a cada 40 min no servidor: confere a faixa a cada 2 min, sem piscar
  useIntervalo(() => recarregar({ silencioso: true }), 2 * 60 * 1000)

  if (!itens.length) return null
  const atual = itens[indice % itens.length]

  return (
    <div className="urgente">
      <div className="container urgente__linha">
        <span className="urgente__selo">
          <span className="urgente__pulso" aria-hidden="true" />
          Urgente
        </span>
        <Link to={`/noticia/${atual.slug}`} className="urgente__titulo">
          {atual.titulo}
        </Link>
      </div>
    </div>
  )
}
