import { Link } from 'react-router-dom'

import useRequisicao from '../hooks/useRequisicao'
import { catalogo } from '../services/noticias'

export default function Rodape() {
  const { dados } = useRequisicao(() => catalogo.categorias(), [])
  const categorias = Array.isArray(dados) ? dados : dados?.results || []
  const ano = new Date().getFullYear()

  return (
    <footer className="rodape">
      <div className="container">
        <div className="rodape__grade">
          <div className="rodape__marca">
            <strong className="marca">Pauta<span className="marca__ponto" aria-hidden="true" /></strong>
            <p style={{ color: 'var(--grafite)', fontSize: 'var(--t-sm)', marginTop: 8 }}>
              Jornalismo direto ao ponto, com cobertura ao vivo e um feed que respeita
              o que você escolhe ler.
            </p>
          </div>
          <div>
            <h4>Editorias</h4>
            <ul>
              {categorias.slice(0, 6).map((categoria) => (
                <li key={categoria.id}>
                  <Link to={`/categoria/${categoria.slug}`}>{categoria.nome}</Link>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4>Navegue</h4>
            <ul>
              <li><Link to="/tendencias">Tendências</Link></li>
              <li><Link to="/mais-lidas">Mais lidas</Link></li>
              <li><Link to="/ao-vivo">Ao vivo</Link></li>
              <li><Link to="/videos">Vídeos</Link></li>
            </ul>
          </div>
          <div>
            <h4>Sua conta</h4>
            <ul>
              <li><Link to="/meus-favoritos">Notícias salvas</Link></li>
              <li><Link to="/historico">Histórico</Link></li>
              <li><Link to="/interesses">Interesses</Link></li>
              <li><Link to="/perfil">Perfil</Link></li>
            </ul>
          </div>
        </div>
        <div className="rodape__base">
          <span>© {ano} Pauta. Feito por: Brito Soluções em TI</span>
          <span>Notícias em tempo real</span>
        </div>
      </div>
    </footer>
  )
}
