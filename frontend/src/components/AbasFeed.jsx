export default function AbasFeed({ abas, ativa, aoTrocar }) {
  return (
    <div className="abas" role="tablist" aria-label="Seções do feed">
      {abas.map((aba) => (
        <button
          key={aba.chave}
          type="button"
          role="tab"
          aria-selected={ativa === aba.chave}
          onClick={() => aoTrocar(aba.chave)}
        >
          {aba.rotulo}
        </button>
      ))}
    </div>
  )
}
