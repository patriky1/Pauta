import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import useDebounce from '../hooks/useDebounce'
import { catalogo } from '../services/noticias'
import { tempoRelativo } from '../utils/formatar'
import Icone from './Icone'

export default function BarraBusca({ aoNavegar, autoFoco = false }) {
  const [termo, setTermo] = useState('')
  const [resultados, setResultados] = useState(null)
  const [aberto, setAberto] = useState(false)
  const [buscando, setBuscando] = useState(false)
  const termoAtrasado = useDebounce(termo, 300)
  const navegar = useNavigate()
  const caixa = useRef(null)
  const campo = useRef(null)

  useEffect(() => {
    if (autoFoco) campo.current?.focus()
  }, [autoFoco])

  useEffect(() => {
    let ativo = true
    if (termoAtrasado.trim().length < 2) {
      setResultados(null)
      setBuscando(false)
      return undefined
    }
    setBuscando(true)
    catalogo
      .buscar({ q: termoAtrasado.trim(), page_size: 5 })
      .then((dados) => {
        if (ativo) {
          setResultados(dados)
          setAberto(true)
        }
      })
      .catch(() => null)
      .finally(() => { if (ativo) setBuscando(false) })
    return () => { ativo = false }
  }, [termoAtrasado])

  useEffect(() => {
    const aoClicarFora = (evento) => {
      if (caixa.current && !caixa.current.contains(evento.target)) setAberto(false)
    }
    document.addEventListener('mousedown', aoClicarFora)
    return () => document.removeEventListener('mousedown', aoClicarFora)
  }, [])

  const fechar = () => {
    setAberto(false)
    setTermo('')
    aoNavegar?.()
  }

  const enviar = (evento) => {
    evento.preventDefault()
    const texto = termo.trim()
    if (texto.length < 2) return
    fechar()
    navegar(`/busca?q=${encodeURIComponent(texto)}`)
  }

  return (
    <form className="busca" role="search" onSubmit={enviar} ref={caixa}>
      <span className="busca__icone" aria-hidden="true"><Icone nome="busca" tamanho={16} /></span>
      <label className="sr-only" htmlFor={autoFoco ? 'campo-busca-movel' : 'campo-busca'}>Buscar notícias</label>
      <input
        ref={campo}
        id={autoFoco ? 'campo-busca-movel' : 'campo-busca'}
        type="search"
        value={termo}
        placeholder="Buscar notícias, autores e assuntos"
        onChange={(evento) => setTermo(evento.target.value)}
        onFocus={() => resultados && setAberto(true)}
        onKeyDown={(evento) => { if (evento.key === 'Escape') setAberto(false) }}
        autoComplete="off"
        enterKeyHint="search"
      />
      {aberto && resultados ? (
        <div className="busca__resultados">
          {resultados.noticias?.length ? (
            resultados.noticias.slice(0, 5).map((noticia) => (
              <Link key={noticia.id} to={`/noticia/${noticia.slug}`} onClick={fechar}>
                {noticia.titulo}
                <small>{noticia.categoria?.nome} · {tempoRelativo(noticia.data_publicacao)}</small>
              </Link>
            ))
          ) : (
            <p style={{ padding: 10, margin: 0, fontSize: 'var(--t-sm)', color: 'var(--grafite)' }}>
              {buscando ? 'Buscando…' : `Nada encontrado para “${termoAtrasado}”.`}
            </p>
          )}
          {resultados.total > 0 ? (
            <button type="submit" className="botao botao--bloco" style={{ marginTop: 6 }}>
              Ver {resultados.total === 1 ? 'o resultado' : `os ${resultados.total} resultados`}
            </button>
          ) : null}
        </div>
      ) : null}
    </form>
  )
}
