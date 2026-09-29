import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { tokens } from '../services/api'
import { autenticacao } from '../services/autenticacao'
import { PAPEIS_REDACAO } from '../utils/constantes'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    let ativo = true
    async function carregar() {
      if (!tokens.acesso()) { setCarregando(false); return }
      try {
        const perfil = await autenticacao.perfil()
        if (ativo) setUsuario(perfil)
      } catch {
        tokens.limpar()
      } finally {
        if (ativo) setCarregando(false)
      }
    }
    carregar()
    return () => { ativo = false }
  }, [])

  useEffect(() => {
    const encerrar = () => setUsuario(null)
    window.addEventListener('pauta:sessao-expirada', encerrar)
    return () => window.removeEventListener('pauta:sessao-expirada', encerrar)
  }, [])

  const entrar = useCallback(async (login, senha) => {
    const perfil = await autenticacao.entrar(login, senha)
    setUsuario(perfil)
    return perfil
  }, [])

  const cadastrar = useCallback(async (dados) => {
    const perfil = await autenticacao.cadastrar(dados)
    setUsuario(perfil)
    return perfil
  }, [])

  const sair = useCallback(async () => {
    await autenticacao.sair()
    setUsuario(null)
  }, [])

  const valor = useMemo(
    () => ({
      usuario,
      carregando,
      autenticado: Boolean(usuario),
      ehRedacao: Boolean(usuario && PAPEIS_REDACAO.includes(usuario.tipo_usuario)),
      ehAdmin: Boolean(usuario && ['ADMIN', 'EDITOR'].includes(usuario.tipo_usuario)),
      entrar,
      cadastrar,
      sair,
      setUsuario,
    }),
    [usuario, carregando, entrar, cadastrar, sair]
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const contexto = useContext(AuthContext)
  if (!contexto) throw new Error('useAuth precisa estar dentro de AuthProvider')
  return contexto
}
