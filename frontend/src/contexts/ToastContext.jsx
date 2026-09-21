import { createContext, useCallback, useContext, useMemo, useState } from 'react'

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
  const [itens, setItens] = useState([])

  const fechar = useCallback((id) => {
    setItens((atuais) => atuais.filter((item) => item.id !== id))
  }, [])

  const mostrar = useCallback(
    (mensagem, tipo = 'info') => {
      const id = Date.now() + Math.random()
      setItens((atuais) => [...atuais, { id, mensagem, tipo }])
      setTimeout(() => fechar(id), 4500)
    },
    [fechar]
  )

  const valor = useMemo(
    () => ({
      mostrar,
      sucesso: (mensagem) => mostrar(mensagem, 'sucesso'),
      erro: (mensagem) => mostrar(mensagem, 'erro'),
    }),
    [mostrar]
  )

  return (
    <ToastContext.Provider value={valor}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {itens.map((item) => (
          <div key={item.id} className={`toast toast--${item.tipo}`}>
            <span>{item.mensagem}</span>
            <button type="button" onClick={() => fechar(item.id)} aria-label="Fechar aviso">
              ✕
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export const useToast = () => {
  const contexto = useContext(ToastContext)
  if (!contexto) throw new Error('useToast precisa estar dentro de ToastProvider')
  return contexto
}
