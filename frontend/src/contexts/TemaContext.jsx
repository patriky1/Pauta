import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

const TemaContext = createContext(null)
const CHAVE = 'pauta.tema'

function temaInicial() {
  const salvo = localStorage.getItem(CHAVE)
  if (salvo) return salvo
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'escuro' : 'claro'
}

export function TemaProvider({ children }) {
  const [tema, setTema] = useState(temaInicial)

  useEffect(() => {
    document.documentElement.dataset.tema = tema
    localStorage.setItem(CHAVE, tema)
    document.querySelector('meta[name="theme-color"]')
      ?.setAttribute('content', tema === 'escuro' ? '#0b0f18' : '#ffffff')
  }, [tema])

  const alternar = useCallback(() => {
    setTema((atual) => (atual === 'escuro' ? 'claro' : 'escuro'))
  }, [])

  const valor = useMemo(() => ({ tema, alternar, setTema }), [tema, alternar])
  return <TemaContext.Provider value={valor}>{children}</TemaContext.Provider>
}

export function useTema() {
  const contexto = useContext(TemaContext)
  if (!contexto) throw new Error('useTema precisa estar dentro de TemaProvider')
  return contexto
}
