const PREFIXO = 'pauta.'

export const guardar = (chave, valor) => {
  try {
    localStorage.setItem(PREFIXO + chave, JSON.stringify(valor))
  } catch {
    /* modo privado ou cota cheia: seguimos sem persistir */
  }
}

export const ler = (chave, padrao = null) => {
  try {
    const bruto = localStorage.getItem(PREFIXO + chave)
    return bruto ? JSON.parse(bruto) : padrao
  } catch {
    return padrao
  }
}

export const remover = (chave) => {
  try {
    localStorage.removeItem(PREFIXO + chave)
  } catch {
    /* ignora */
  }
}

export const CHAVES = {
  acesso: 'token_acesso',
  refresh: 'token_refresh',
  tema: 'tema',
  modoLeitura: 'modo_leitura',
  feed: 'feed_preferido',
}
