import { useCallback, useEffect, useRef, useState } from 'react'

import { mensagemDeErro } from '../services/api'

/** Lista paginada com "carregar mais", protegida contra respostas fora de ordem. */
export default function useListaPaginada(buscar, dependencias = []) {
  const [itens, setItens] = useState([])
  const [pagina, setPagina] = useState(1)
  const [temMais, setTemMais] = useState(false)
  const [total, setTotal] = useState(0)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState(null)

  const buscarRef = useRef(buscar)
  const ultimaRequisicao = useRef(0)
  const montado = useRef(false)
  buscarRef.current = buscar

  useEffect(() => {
    montado.current = true
    return () => {
      montado.current = false
    }
  }, [])

  const carregar = useCallback(
    async (numero) => {
      const id = ++ultimaRequisicao.current
      setCarregando(true)
      setErro(null)
      if (numero === 1) setItens([])
      try {
        const dados = await buscarRef.current(numero)
        if (!montado.current || id !== ultimaRequisicao.current) return
        const resultados = Array.isArray(dados) ? dados : dados?.results || []
        setItens((anteriores) => (numero === 1 ? resultados : [...anteriores, ...resultados]))
        setTemMais(Boolean(dados?.next))
        setTotal(dados?.count ?? resultados.length)
        setPagina(numero)
      } catch (falha) {
        if (montado.current && id === ultimaRequisicao.current) setErro(mensagemDeErro(falha))
      } finally {
        if (montado.current && id === ultimaRequisicao.current) setCarregando(false)
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    dependencias
  )

  useEffect(() => {
    carregar(1)
  }, [carregar])

  return {
    itens,
    total,
    temMais,
    carregando,
    erro,
    pagina,
    carregarMais: () => carregar(pagina + 1),
    recarregar: () => carregar(1),
    setItens,
  }
}
