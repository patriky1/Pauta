import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext'
import useSeo from '../hooks/useSeo'
import { mensagemDeErro } from '../services/api'

export default function Cadastrar() {
  const { cadastrar } = useAuth()
  const navegar = useNavigate()
  const [form, setForm] = useState({ nome: '', username: '', email: '', password: '', password_confirm: '' })
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  useSeo({ titulo: 'Criar conta', caminho: '/cadastrar' })

  const trocar = (campo) => (evento) => setForm({ ...form, [campo]: evento.target.value })

  const enviar = async (evento) => {
    evento.preventDefault()
    setErro('')
    if (form.password !== form.password_confirm) { setErro('As senhas não conferem.'); return }
    setEnviando(true)
    try {
      await cadastrar(form)
      navegar('/interesses', { replace: true })
    } catch (falha) {
      setErro(mensagemDeErro(falha))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="container">
      <form className="formulario formulario--cartao" onSubmit={enviar} noValidate={false}>
        <h1 className="formulario__titulo">Criar conta</h1>
        <p className="formulario__subtitulo">Leva menos de um minuto. Depois você escolhe as editorias que quer acompanhar.</p>
        {erro ? <div className="aviso" role="alert">{erro}</div> : null}

        <div className="campo">
          <label htmlFor="nome">Nome</label>
          <input id="nome" value={form.nome} onChange={trocar('nome')} required />
        </div>
        <div className="campo">
          <label htmlFor="username">Nome de usuário</label>
          <input id="username" value={form.username} onChange={trocar('username')} required autoComplete="username" />
        </div>
        <div className="campo">
          <label htmlFor="email">E-mail</label>
          <input id="email" type="email" value={form.email} onChange={trocar('email')} required autoComplete="email" />
        </div>
        <div className="campo">
          <label htmlFor="senha">Senha</label>
          <input id="senha" type="password" value={form.password} onChange={trocar('password')} required minLength={8} autoComplete="new-password" />
          <span className="campo__ajuda">Use ao menos 8 caracteres, misturando letras e números.</span>
        </div>
        <div className="campo">
          <label htmlFor="senha2">Repita a senha</label>
          <input id="senha2" type="password" value={form.password_confirm} onChange={trocar('password_confirm')} required autoComplete="new-password" />
        </div>

        <button type="submit" className="botao botao--primario botao--bloco" disabled={enviando}>
          {enviando ? 'Criando…' : 'Criar conta'}
        </button>

        <p className="formulario__rodape">
          Já tem conta? <Link to="/entrar">Entrar</Link>
        </p>
      </form>
    </div>
  )
}
