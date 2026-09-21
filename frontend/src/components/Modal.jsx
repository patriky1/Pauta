import { useEffect, useRef } from 'react'

import Icone from './Icone'

export default function Modal({ aberto, titulo, aoFechar, children, rodape, largo = false }) {
  const referencia = useRef(null)

  useEffect(() => {
    if (!aberto) return undefined
    const aoTeclar = (evento) => { if (evento.key === 'Escape') aoFechar?.() }
    const anterior = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', aoTeclar)
    referencia.current?.focus()
    return () => {
      document.body.style.overflow = anterior
      document.removeEventListener('keydown', aoTeclar)
    }
  }, [aberto, aoFechar])

  if (!aberto) return null

  return (
    <div className="modal-fundo" onMouseDown={(e) => e.target === e.currentTarget && aoFechar?.()}>
      <div
        className={`modal${largo ? ' modal--largo' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        tabIndex={-1}
        ref={referencia}
      >
        <div className="modal__cabecalho">
          <h2 className="modal__titulo">{titulo}</h2>
          <button type="button" className="icone-botao" onClick={aoFechar} aria-label="Fechar">
            <Icone nome="fechar" tamanho={18} />
          </button>
        </div>
        {children}
        {rodape ? <div style={{ marginTop: 'var(--e-4)' }}>{rodape}</div> : null}
      </div>
    </div>
  )
}
