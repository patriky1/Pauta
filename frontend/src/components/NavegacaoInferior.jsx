import { NavLink } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext'
import Icone from './Icone'

/** Barra de navegação fixa no rodapé, visível apenas em telas de celular. */
export default function NavegacaoInferior() {
  const { autenticado } = useAuth()

  const itens = [
    { para: '/', rotulo: 'Início', icone: 'casa', fim: true },
    { para: '/busca', rotulo: 'Buscar', icone: 'busca' },
    { para: '/ao-vivo', rotulo: 'Ao vivo', icone: 'raio' },
    { para: '/meus-favoritos', rotulo: 'Salvos', icone: 'marcadorVazio' },
    { para: autenticado ? '/perfil' : '/entrar', rotulo: autenticado ? 'Conta' : 'Entrar', icone: 'usuario' },
  ]

  return (
    <nav className="nav-inferior" aria-label="Navegação rápida">
      <div className="nav-inferior__lista">
        {itens.map((item) => (
          <NavLink
            key={item.rotulo}
            to={item.para}
            end={item.fim}
            className={({ isActive }) => (isActive ? 'ativo' : undefined)}
          >
            <Icone nome={item.icone} tamanho={21} />
            {item.rotulo}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
