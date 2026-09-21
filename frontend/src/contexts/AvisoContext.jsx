import { createContext, useCallback, useContext, useMemo, useState } from 'react'

const AvisoContext = createContext(null)

export function AvisoProvider({ children }) {
  const [avisos, setAvisos] = useState([])

  const remover = useCallback((id) => {
    setAvisos((atuais) => atuais.filter((aviso) => aviso.id !== id))
  }, [])

  const mostrar = useCallback(
    (texto, tipo = 'info') => {
      const id = Date.now() + Math.random()
      setAvisos((atuais) => [...atuais, { id, texto, tipo }])
      setTimeout(() => remover(id), 4200)
    },
    [remover]
  )

  const valor = useMemo(() => ({ avisos, mostrar, remover }), [avisos, mostrar, remover])

  return (
    <AvisoContext.Provider value={valor}>
      {children}
      <div className="torradeira" role="status" aria-live="polite">
        {avisos.map((aviso) => (
          <div key={aviso.id} className={`torrada${aviso.tipo === 'erro' ? ' torrada--erro' : ''}`}>
            {aviso.texto}
          </div>
        ))}
      </div>
    </AvisoContext.Provider>
  )
}

export function useAviso() {
  const contexto = useContext(AvisoContext)
  if (!contexto) throw new Error('useAviso precisa estar dentro de AvisoProvider')
  return contexto
}
