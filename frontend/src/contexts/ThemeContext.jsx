import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { CHAVES, guardar, ler } from '../utils/armazenamento'

const ThemeContext = createContext(null)

function temaInicial() {
  const salvo = ler(CHAVES.tema)
  if (salvo) return salvo
  const prefereEscuro = window.matchMedia?.('(prefers-color-scheme: dark)').matches
  return prefereEscuro ? 'escuro' : 'claro'
}

export function ThemeProvider({ children }) {
  const [tema, setTema] = useState(temaInicial)
  const [modoLeitura, setModoLeitura] = useState(() => ler(CHAVES.modoLeitura, false))

  useEffect(() => {
    document.documentElement.dataset.tema = tema
    document
      .querySelector('meta[name="theme-color"]')
      ?.setAttribute('content', tema === 'escuro' ? '#0c111c' : '#101522')
    guardar(CHAVES.tema, tema)
  }, [tema])

  useEffect(() => {
    document.body.classList.toggle('modo-leitura', modoLeitura)
    guardar(CHAVES.modoLeitura, modoLeitura)
  }, [modoLeitura])

  const alternarTema = useCallback(
    () => setTema((atual) => (atual === 'escuro' ? 'claro' : 'escuro')),
    []
  )
  const alternarModoLeitura = useCallback(() => setModoLeitura((atual) => !atual), [])

  return (
    <ThemeContext.Provider value={{ tema, alternarTema, modoLeitura, alternarModoLeitura }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTema = () => {
  const contexto = useContext(ThemeContext)
  if (!contexto) throw new Error('useTema precisa estar dentro de ThemeProvider')
  return contexto
}
