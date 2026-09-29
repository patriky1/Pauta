import { useCallback, useEffect, useRef, useState } from 'react'

import { mensagemDeErro } from '../services/api'

/**
 * Executa uma função assíncrona e devolve { dados, carregando, erro }.
 *
 * - Compatível com o StrictMode do React 18 (montagem dupla em desenvolvimento).
 * - Ignora respostas antigas quando as dependências mudam antes da anterior terminar.
 * - `recarregar({ silencioso: true })` atualiza sem voltar ao estado de carregamento,
 *   evitando o "pisca" do skeleton em atualizações periódicas (ex.: ao vivo).
 */
export default function useRequisicao(funcao, dependencias = [], { ativo = true } = {}) {
  const [dados, setDados] = useState(null)
  const [carregando, setCarregando] = useState(ativo)
  const [erro, setErro] = useState(null)

  const funcaoRef = useRef(funcao)
  const montado = useRef(false)
  const ultimaRequisicao = useRef(0)

  funcaoRef.current = funcao

  useEffect(() => {
    montado.current = true
    return () => {
      montado.current = false
    }
  }, [])

  const executar = useCallback(
    async ({ silencioso = false } = {}) => {
      if (!ativo) {
        setCarregando(false)
        return
      }
      const id = ++ultimaRequisicao.current
      if (!silencioso) setCarregando(true)
      setErro(null)
      try {
        const resultado = await funcaoRef.current()
        if (montado.current && id === ultimaRequisicao.current) setDados(resultado)
      } catch (falha) {
        if (montado.current && id === ultimaRequisicao.current && !silencioso) {
          setErro(mensagemDeErro(falha))
        }
      } finally {
        if (montado.current && id === ultimaRequisicao.current) setCarregando(false)
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [ativo, ...dependencias]
  )

  useEffect(() => {
    executar()
  }, [executar])

  return { dados, carregando, erro, recarregar: executar, setDados }
}
