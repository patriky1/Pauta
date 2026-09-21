import { useState } from 'react'

/**
 * Imagem com proporção reservada (sem salto de layout), carregamento preguiçoso
 * e reserva visual quando a URL falha ou não existe.
 */
export default function Imagem({ src, alt = '', className = '', prioridade = false, largura, altura, estilo }) {
  const [estado, setEstado] = useState(src ? 'carregando' : 'erro')

  return (
    <div
      className={`imagem${estado === 'carregando' ? ' imagem--carregando' : ''} ${className}`.trim()}
      style={estilo}
    >
      {src && estado !== 'erro' ? (
        <img
          src={src}
          alt={alt}
          width={largura}
          height={altura}
          loading={prioridade ? 'eager' : 'lazy'}
          decoding="async"
          ref={(elemento) => {
            // atributo definido direto no DOM: compatível com React 18 e 19 sem avisos
            if (elemento && prioridade) elemento.setAttribute('fetchpriority', 'high')
          }}
          onLoad={() => setEstado('ok')}
          onError={() => setEstado('erro')}
        />
      ) : null}
      {estado === 'erro' ? (
        <span className="imagem__reserva" aria-hidden="true">
          Pauta<span style={{ color: 'var(--sinal)' }}>.</span>
        </span>
      ) : null}
    </div>
  )
}
