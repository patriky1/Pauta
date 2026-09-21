import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import GradeNoticias from '../components/GradeNoticias'

describe('GradeNoticias', () => {
  it('mostra estado vazio quando não há notícias', () => {
    render(
      <MemoryRouter>
        <GradeNoticias noticias={[]} carregando={false} vazioTitulo="Sem notícias aqui" />
      </MemoryRouter>
    )
    expect(screen.getByText('Sem notícias aqui')).toBeInTheDocument()
  })

  it('mostra o erro e o botão de tentar de novo', () => {
    render(
      <MemoryRouter>
        <GradeNoticias noticias={[]} erro="Falha na rede" aoRecarregar={() => {}} />
      </MemoryRouter>
    )
    expect(screen.getByText('Falha na rede')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /tentar de novo/i })).toBeInTheDocument()
  })
})
