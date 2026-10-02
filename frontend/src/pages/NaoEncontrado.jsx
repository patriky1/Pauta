import { Link } from 'react-router-dom'

import useSeo from '../hooks/useSeo'

export default function NaoEncontrado() {
  useSeo({ titulo: 'Página não encontrada' })
  return (
    <div className="container">
      <div className="estado" style={{ padding: 'var(--e-7) 0' }}>
        <p style={{ fontFamily: 'var(--fonte-titulo)', fontSize: 'var(--t-4xl)', fontWeight: 700, color: 'var(--sinal)', margin: 0 }}>
          404
        </p>
        <h1 style={{ fontSize: 'var(--t-2xl)', color: 'var(--tinta)', margin: '8px 0' }}>Esta página saiu do ar</h1>
        <p>O endereço pode ter mudado ou a matéria foi arquivada.</p>
        <div className="grupo-botoes" style={{ justifyContent: 'center' }}>
          <Link to="/" className="botao botao--primario">Voltar para a home</Link>
          <Link to="/busca" className="botao">Buscar uma matéria</Link>
        </div>
      </div>
    </div>
  )
}
