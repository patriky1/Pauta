import { useState } from 'react'
import { Link } from 'react-router-dom'

import useSeo from '../hooks/useSeo'
import { autenticacao } from '../services/autenticacao'

export default function RecuperarSenha() {
  const [email, setEmail] = useState('')
  const [enviado, setEnviado] = useState(false)
  const [enviando, setEnviando] = useState(false)
  useSeo({ titulo: 'Recuperar senha', caminho: '/recuperar-senha' })

  const enviar = async (evento) => {
    evento.preventDefault()
    setEnviando(true)
    await autenticacao.pedirReset(email).catch(() => null)
    setEnviando(false)
    setEnviado(true)
  }

  return (
    <div className="container">
      <form className="formulario formulario--cartao" onSubmit={enviar} noValidate={false}>
        <h1 className="formulario__titulo">Recuperar senha</h1>
        <p className="formulario__subtitulo">Informe o e-mail da sua conta e enviaremos um link para criar uma nova senha.</p>
        {enviado ? (
          <div className="aviso aviso--ok">
            Se este e-mail estiver cadastrado, enviamos um link para criar uma nova senha.
          </div>
        ) : null}
        <div className="campo">
          <label htmlFor="email">Seu e-mail</label>
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <button type="submit" className="botao botao--primario botao--bloco" disabled={enviando}>
          {enviando ? 'Enviando…' : 'Enviar link'}
        </button>
        <p className="formulario__rodape">
          <Link to="/entrar">Voltar para o login</Link>
        </p>
      </form>
    </div>
  )
}
