export function Esqueleto({ altura = 16, largura = '100%', raio = 6, estilo }) {
  return (
    <div
      className="esqueleto"
      style={{ height: altura, width: largura, borderRadius: raio, ...estilo }}
      aria-hidden="true"
    />
  )
}

export function EsqueletoCartao() {
  return (
    <div className="cartao" aria-hidden="true">
      <div className="cartao__link">
        <Esqueleto altura={0} estilo={{ aspectRatio: '16 / 10', width: '100%', borderRadius: 12 }} />
        <div className="cartao__corpo">
          <Esqueleto altura={12} largura="35%" />
          <Esqueleto altura={20} />
          <Esqueleto altura={20} largura="70%" />
          <Esqueleto altura={11} largura="45%" />
        </div>
      </div>
    </div>
  )
}

export function EsqueletoLista({ quantidade = 6 }) {
  return (
    <div className="grade grade--manter" aria-busy="true" aria-label="Carregando">
      {Array.from({ length: quantidade }, (_, indice) => (
        <EsqueletoCartao key={indice} />
      ))}
    </div>
  )
}

export function EsqueletoMateria() {
  return (
    <div className="materia" aria-hidden="true">
      <Esqueleto altura={14} largura="20%" />
      <div style={{ height: 12 }} />
      <Esqueleto altura={38} />
      <div style={{ height: 8 }} />
      <Esqueleto altura={38} largura="80%" />
      <div style={{ height: 24 }} />
      <Esqueleto altura={0} estilo={{ aspectRatio: '16 / 10', borderRadius: 12 }} />
      <div style={{ height: 24 }} />
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} style={{ marginBottom: 10 }}>
          <Esqueleto altura={16} largura={i % 3 === 2 ? '60%' : '100%'} />
        </div>
      ))}
    </div>
  )
}

export default Esqueleto
