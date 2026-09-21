import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext'
import { useAviso } from '../contexts/AvisoContext'
import useSeo from '../hooks/useSeo'
import { mensagemDeErro } from '../services/api'
import { autenticacao } from '../services/autenticacao'

export default function Perfil() {
  const { usuario, setUsuario, ehRedacao, sair } = useAuth()
  const { mostrar } = useAviso()
  const [form, setForm] = useState({
    nome: usuario?.nome || '',
    email: usuario?.email || '',
    biografia: usuario?.biografia || '',
    site: usuario?.site || '',
    twitter: usuario?.twitter || '',
    instagram: usuario?.instagram || '',
    linkedin: usuario?.linkedin || '',
  })
  const [senhas, setSenhas] = useState({ senha_atual: '', nova_senha: '' })
  const [salvando, setSalvando] = useState(false)

  useSeo({ titulo: 'Seu perfil', caminho: '/perfil' })

  const trocar = (campo) => (evento) => setForm({ ...form, [campo]: evento.target.value })

  const salvar = async (evento) => {
    evento.preventDefault()
    setSalvando(true)
    try {
      const atualizado = await autenticacao.atualizarPerfil(form)
      setUsuario(atualizado)
      mostrar('Perfil atualizado.')
    } catch (falha) {
      mostrar(mensagemDeErro(falha), 'erro')
    } finally {
      setSalvando(false)
    }
  }

  const trocarSenha = async (evento) => {
    evento.preventDefault()
    try {
      await autenticacao.alterarSenha(senhas.senha_atual, senhas.nova_senha)
      setSenhas({ senha_atual: '', nova_senha: '' })
      mostrar('Senha alterada.')
    } catch (falha) {
      mostrar(mensagemDeErro(falha), 'erro')
    }
  }

  return (
    <div className="container pagina">
      <section>
        <div className="pagina__cabecalho">
          <div>
            <h1 className="titulo-pagina">Seu perfil</h1>
            <p className="pagina__descricao">@{usuario?.username} · as informações abaixo aparecem no seu perfil público.</p>
          </div>
          <div className="grupo-botoes">
            {ehRedacao ? <Link to="/admin" className="botao">Abrir painel</Link> : null}
            <button type="button" className="botao botao--contorno-perigo" onClick={sair}>Sair da conta</button>
          </div>
        </div>

        <div className="coluna-dupla">
          <form onSubmit={salvar} className="bloco">
            <h2 className="secao__titulo secao__titulo--pequeno" style={{ marginBottom: 'var(--e-4)' }}>Dados pessoais</h2>
            <div className="campo">
              <label htmlFor="nome">Nome</label>
              <input id="nome" value={form.nome} onChange={trocar('nome')} required />
            </div>
            <div className="campo">
              <label htmlFor="email">E-mail</label>
              <input id="email" type="email" value={form.email} onChange={trocar('email')} required />
            </div>
            <div className="campo">
              <label htmlFor="biografia">Biografia</label>
              <textarea id="biografia" value={form.biografia} onChange={trocar('biografia')} />
            </div>
            <div className="campos-linha">
              <div className="campo">
                <label htmlFor="site">Site</label>
                <input id="site" value={form.site} onChange={trocar('site')} placeholder="https://" />
              </div>
              <div className="campo">
                <label htmlFor="twitter">X</label>
                <input id="twitter" value={form.twitter} onChange={trocar('twitter')} placeholder="@usuario" />
              </div>
              <div className="campo">
                <label htmlFor="instagram">Instagram</label>
                <input id="instagram" value={form.instagram} onChange={trocar('instagram')} />
              </div>
              <div className="campo">
                <label htmlFor="linkedin">LinkedIn</label>
                <input id="linkedin" value={form.linkedin} onChange={trocar('linkedin')} />
              </div>
            </div>
            <button type="submit" className="botao botao--primario" disabled={salvando}>
              {salvando ? 'Salvando…' : 'Salvar alterações'}
            </button>
          </form>

          <aside className="lateral">
            <form onSubmit={trocarSenha} className="bloco">
              <h2 style={{ fontSize: 'var(--t-xl)', marginBottom: 'var(--e-3)' }}>Trocar senha</h2>
              <div className="campo">
                <label htmlFor="atual">Senha atual</label>
                <input
                  id="atual"
                  type="password"
                  value={senhas.senha_atual}
                  onChange={(e) => setSenhas({ ...senhas, senha_atual: e.target.value })}
                  required
                />
              </div>
              <div className="campo">
                <label htmlFor="nova">Nova senha</label>
                <input
                  id="nova"
                  type="password"
                  value={senhas.nova_senha}
                  onChange={(e) => setSenhas({ ...senhas, nova_senha: e.target.value })}
                  required
                  minLength={8}
                />
              </div>
              <button type="submit" className="botao botao--bloco">Atualizar senha</button>
            </form>
            <nav className="bloco" aria-label="Atalhos da conta">
              <h2 style={{ fontSize: 'var(--t-xl)', marginBottom: 'var(--e-2)' }}>Atalhos</h2>
              <Link className="suspenso__item" to="/interesses">Editar interesses</Link>
              <Link className="suspenso__item" to="/meus-favoritos">Notícias salvas</Link>
              <Link className="suspenso__item" to="/historico">Histórico de leitura</Link>
            </nav>
          </aside>
        </div>
      </section>
    </div>
  )
}
