import { useEffect, useState } from 'react'

export default function useDebounce(valor, atraso = 350) {
  const [atrasado, setAtrasado] = useState(valor)

  useEffect(() => {
    const id = setTimeout(() => setAtrasado(valor), atraso)
    return () => clearTimeout(id)
  }, [valor, atraso])

  return atrasado
}
