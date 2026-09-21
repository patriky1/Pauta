import { useEffect, useRef } from 'react'

/** Repete uma chamada em intervalo fixo (coberturas ao vivo, notificações). */
export default function useIntervalo(funcao, intervalo) {
  const salvo = useRef(funcao)

  useEffect(() => { salvo.current = funcao }, [funcao])

  useEffect(() => {
    if (!intervalo) return undefined
    const id = setInterval(() => salvo.current(), intervalo)
    return () => clearInterval(id)
  }, [intervalo])
}
