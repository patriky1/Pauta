import { describe, expect, it } from 'vitest'

import { duracao, iniciais, numero, tempoRelativo } from '../utils/formatar'

describe('formatadores', () => {
  it('compacta números grandes', () => {
    expect(numero(12000)).toMatch(/12/)
  })

  it('formata duração em minutos e segundos', () => {
    expect(duracao(125)).toBe('2:05')
  })

  it('extrai as iniciais do nome', () => {
    expect(iniciais('Beatriz Lima Souza')).toBe('BL')
  })

  it('descreve datas recentes como tempo relativo', () => {
    const duasHorasAtras = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
    expect(tempoRelativo(duasHorasAtras)).toContain('hora')
  })
})
