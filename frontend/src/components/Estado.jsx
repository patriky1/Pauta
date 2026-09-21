import Icone from './Icone'

export function EstadoVazio({ titulo = 'Nada por aqui ainda', descricao, acao, icone = 'leitura' }) {
  return (
    <div className="estado">
      <div className="estado__icone" aria-hidden="true"><Icone nome={icone} tamanho={22} /></div>
      <h3>{titulo}</h3>
      {descricao ? <p>{descricao}</p> : null}
      {acao}
    </div>
  )
}

export function EstadoErro({ mensagem = 'Não foi possível carregar.', aoTentarNovamente }) {
  return (
    <div className="estado" role="alert">
      <div className="estado__icone" aria-hidden="true" style={{ color: 'var(--sinal)' }}>
        <Icone nome="raio" tamanho={22} />
      </div>
      <h3>Não conseguimos carregar</h3>
      <p>{mensagem}</p>
      {aoTentarNovamente ? (
        <button type="button" className="botao" onClick={() => aoTentarNovamente()}>
          Tentar de novo
        </button>
      ) : null}
    </div>
  )
}

export default EstadoVazio
