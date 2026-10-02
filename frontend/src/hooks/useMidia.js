import { useEffect, useState } from 'react'

/** Retorna true quando a media query casa (ex.: '(max-width: 760px)'). */
export default function useMidia(consulta) {
  const [casa, setCasa] = useState(() =>
    typeof window !== 'undefined' ? window.matchMedia(consulta).matches : false
  )

  useEffect(() => {
    const lista = window.matchMedia(consulta)
    const aoMudar = () => setCasa(lista.matches)
    aoMudar()
    lista.addEventListener('change', aoMudar)
    return () => lista.removeEventListener('change', aoMudar)
  }, [consulta])

  return casa
}
