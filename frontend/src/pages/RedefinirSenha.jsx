import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import useSeo from '../hooks/useSeo'
import { mensagemDeErro } from '../services/api'
import { autenticacao } from '../services/autenticacao'

export default function RedefinirSenha() {
  const [parametros] = useSearchParams()
  const navegar = useNavigate()
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)
  useSeo({ titulo: 'Criar nova senha', caminho: '/redefinir-senha' })

  const enviar = async (evento) => {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await autenticacao.confirmarReset(parametros.get('uid'), parametros.get('token'), senha)
      navegar('/entrar', { replace: true })
    } catch (falha) {
      setErro(mensagemDeErro(falha))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="container">
      <form className="formulario formulario--cartao" onSubmit={enviar} noValidate={false}>
        <h1 className="formulario__titulo">Criar nova senha</h1>
        <p className="formulario__subtitulo">Escolha uma senha nova com pelo menos 8 caracteres.</p>
        {erro ? <div className="aviso" role="alert">{erro}</div> : null}
        <div className="campo">
          <label htmlFor="senha">Nova senha</label>
          <input id="senha" type="password" value={senha} onChange={(e) => setSenha(e.target.value)} required minLength={8} />
        </div>
        <button type="submit" className="botao botao--primario botao--bloco" disabled={enviando}>
          {enviando ? 'Salvando…' : 'Salvar nova senha'}
        </button>
      </form>
    </div>
  )
}
