import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'

import BotaoTema from '../components/BotaoTema'
import LimiteErro from '../components/LimiteErro'
import { useAuth } from '../contexts/AuthContext'

const ITENS = [
  { para: '/admin', rotulo: 'Visão geral', fim: true },
  { para: '/admin/noticias', rotulo: 'Notícias', fim: true },
  { para: '/admin/noticias/nova', rotulo: 'Nova notícia' },
  { para: '/admin/ao-vivo', rotulo: 'Ao vivo' },
  { para: '/admin/moderacao', rotulo: 'Moderação', somenteEditor: true },
  { para: '/admin/usuarios', rotulo: 'Usuários', somenteEditor: true },
]

export default function LayoutPainel() {
  const { usuario, ehAdmin } = useAuth()
  const { pathname } = useLocation()
  const itens = ehAdmin ? ITENS : ITENS.filter((item) => !item.somenteEditor)

  return (
    <div className="painel">
      <aside className="painel__menu">
        <Link to="/" className="marca" style={{ fontSize: '1.3rem' }} title="Voltar ao site">
          Pauta<span className="marca__ponto" aria-hidden="true" />
        </Link>
        <nav className="painel__nav" aria-label="Painel">
          {itens.map((item) => (
            <NavLink
              key={item.para}
              to={item.para}
              end={item.fim}
              className={({ isActive }) => (isActive ? 'ativo' : undefined)}
            >
              {item.rotulo}
            </NavLink>
          ))}
        </nav>
        <div className="painel__rodape">
          <BotaoTema />
          <span>{usuario?.nome}</span>
        </div>
      </aside>
      <div className="painel__conteudo">
        <LimiteErro chave={pathname}>
          <Outlet />
        </LimiteErro>
      </div>
    </div>
  )
}
