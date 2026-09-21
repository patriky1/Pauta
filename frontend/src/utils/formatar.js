const RTF = new Intl.RelativeTimeFormat('pt-BR', { numeric: 'auto' })

/**
 * Converte o valor em Date. Datas puras ("2026-09-20") são lidas no fuso local —
 * o construtor padrão as trata como UTC e, no Brasil, exibiria o dia anterior.
 */
export function paraData(valor) {
  if (valor instanceof Date) return valor
  if (typeof valor === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(valor)) {
    const [ano, mes, dia] = valor.split('-').map(Number)
    return new Date(ano, mes - 1, dia)
  }
  const data = new Date(valor)
  return Number.isNaN(data.getTime()) ? null : data
}

export function dataCompleta(valor) {
  if (!valor || !paraData(valor)) return ''
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(paraData(valor))
}

export function dataCurta(valor) {
  if (!valor || !paraData(valor)) return ''
  return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit', year: '2-digit' })
    .format(paraData(valor))
}

export function hora(valor) {
  if (!valor || !paraData(valor)) return ''
  return new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' })
    .format(paraData(valor))
}

export function tempoRelativo(valor) {
  const data = valor ? paraData(valor) : null
  if (!data) return ''
  const segundos = (data.getTime() - Date.now()) / 1000
  const faixas = [
    ['year', 60 * 60 * 24 * 365],
    ['month', 60 * 60 * 24 * 30],
    ['day', 60 * 60 * 24],
    ['hour', 60 * 60],
    ['minute', 60],
  ]
  for (const [unidade, tamanho] of faixas) {
    if (Math.abs(segundos) >= tamanho) return RTF.format(Math.round(segundos / tamanho), unidade)
  }
  return 'agora'
}

export function numero(valor) {
  return new Intl.NumberFormat('pt-BR', { notation: 'compact' }).format(valor || 0)
}

export function duracao(segundos) {
  const m = Math.floor((segundos || 0) / 60)
  const s = Math.floor((segundos || 0) % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

export function iniciais(nome = '') {
  return String(nome || '?').trim().split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]).join('').toUpperCase() || '?'
}
