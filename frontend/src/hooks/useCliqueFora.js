import { useEffect } from 'react'

export default function useCliqueFora(referencia, aoFechar, ativo = true) {
  useEffect(() => {
    if (!ativo) return undefined
    const clique = (evento) => {
      if (referencia.current && !referencia.current.contains(evento.target)) aoFechar()
    }
    const tecla = (evento) => {
      if (evento.key === 'Escape') aoFechar()
    }
    document.addEventListener('mousedown', clique)
    document.addEventListener('keydown', tecla)
    return () => {
      document.removeEventListener('mousedown', clique)
      document.removeEventListener('keydown', tecla)
    }
  }, [referencia, aoFechar, ativo])
}
