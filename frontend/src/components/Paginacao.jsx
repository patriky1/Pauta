export default function Paginacao({ pagina, temMais, carregando, aoCarregarMais, total }) {
  if (!temMais && pagina === 1) return null
  return (
    <div className="paginacao">
      {temMais ? (
        <button type="button" className="botao" onClick={aoCarregarMais} disabled={carregando}>
          {carregando ? 'Carregando…' : 'Carregar mais'}
        </button>
      ) : (
        <span>Você chegou ao fim{total ? ` de ${total} resultados` : ''}.</span>
      )}
    </div>
  )
}
