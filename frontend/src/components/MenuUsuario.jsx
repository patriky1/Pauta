import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext'
import { iniciais } from '../utils/formatar'

export default function MenuUsuario() {
  const { usuario, ehRedacao, sair } = useAuth()
  const [aberto, setAberto] = useState(false)
  const caixa = useRef(null)
  const local = useLocation()
  const navegar = useNavigate()

  useEffect(() => { setAberto(false) }, [local.pathname])

  useEffect(() => {
    if (!aberto) return undefined
    const fora = (evento) => {
      if (caixa.current && !caixa.current.contains(evento.target)) setAberto(false)
    }
    const tecla = (evento) => { if (evento.key === 'Escape') setAberto(false) }
    document.addEventListener('mousedown', fora)
    document.addEventListener('keydown', tecla)
    return () => {
      document.removeEventListener('mousedown', fora)
      document.removeEventListener('keydown', tecla)
    }
  }, [aberto])

  if (!usuario) return null

  const encerrar = async () => {
    await sair()
    navegar('/')
  }

  return (
    <div className="suspenso" ref={caixa}>
      <button
        type="button"
        className="icone-botao"
        onClick={() => setAberto((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={aberto}
        aria-label="Menu da conta"
      >
        {usuario.foto ? (
          <img className="avatar avatar--p" src={usuario.foto} alt="" />
        ) : (
          <span className="avatar avatar--p">{iniciais(usuario.nome || usuario.username)}</span>
        )}
      </button>

      {aberto ? (
        <div className="suspenso__painel" role="menu">
          <div className="suspenso__usuario">
            <strong>{usuario.nome}</strong>
            <span>@{usuario.username}</span>
          </div>
          <Link className="suspenso__item" to="/perfil" role="menuitem">Meu perfil</Link>
          <Link className="suspenso__item" to="/meus-favoritos" role="menuitem">Notícias salvas</Link>
          <Link className="suspenso__item" to="/historico" role="menuitem">Histórico</Link>
          <Link className="suspenso__item" to="/interesses" role="menuitem">Meus interesses</Link>
          {ehRedacao ? (
            <Link className="suspenso__item" to="/admin" role="menuitem">Painel da redação</Link>
          ) : null}
          <button type="button" className="suspenso__item suspenso__item--perigo" onClick={encerrar} role="menuitem">
            Sair da conta
          </button>
        </div>
      ) : null}
    </div>
  )
}
