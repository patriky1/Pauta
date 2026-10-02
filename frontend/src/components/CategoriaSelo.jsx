import { Link } from 'react-router-dom'

export default function CategoriaSelo({ categoria, link = true }) {
  if (!categoria) return null
  const estilo = categoria.cor
    ? { color: categoria.cor, background: `color-mix(in srgb, ${categoria.cor} 12%, transparent)` }
    : undefined
  const conteudo = (
    <span className="selo" style={estilo}>
      {categoria.nome}
    </span>
  )
  if (!link) return conteudo
  return <Link to={`/categoria/${categoria.slug}`}>{conteudo}</Link>
}
