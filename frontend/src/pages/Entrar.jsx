import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext'
import useSeo from '../hooks/useSeo'
import { mensagemDeErro } from '../services/api'

export default function Entrar() {
  const { entrar } = useAuth()
  const navegar = useNavigate()
  const local = useLocation()
  const [login, setLogin] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  useSeo({ titulo: 'Entrar', caminho: '/entrar' })

  const enviar = async (evento) => {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await entrar(login, senha)
      navegar(local.state?.de || '/', { replace: true })
    } catch (falha) {
      setErro(mensagemDeErro(falha))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="container">
      <form className="formulario formulario--cartao" onSubmit={enviar} noValidate={false}>
        <h1 className="formulario__titulo">Entrar</h1>
        <p className="formulario__subtitulo">Bem-vindo de volta. Entre para ver seu feed e suas notícias salvas.</p>
        {erro ? <div className="aviso" role="alert">{erro}</div> : null}

        <div className="campo">
          <label htmlFor="login">E-mail ou nome de usuário</label>
          <input id="login" value={login} onChange={(e) => setLogin(e.target.value)} required autoComplete="username" />
        </div>
        <div className="campo">
          <label htmlFor="senha">Senha</label>
          <input id="senha" type="password" value={senha} onChange={(e) => setSenha(e.target.value)} required autoComplete="current-password" />
        </div>

        <button type="submit" className="botao botao--primario botao--bloco" disabled={enviando}>
          {enviando ? 'Entrando…' : 'Entrar'}
        </button>

        <p className="formulario__rodape">
          <Link to="/recuperar-senha">Esqueci minha senha</Link>
          {' · '}
          <Link to="/cadastrar">Criar conta</Link>
        </p>
      </form>
    </div>
  )
}
