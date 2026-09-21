import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import CartaoNoticia from '../components/CartaoNoticia'

const noticia = {
  id: 1,
  titulo: 'Nova política de dados entra em vigor',
  slug: 'nova-politica-de-dados',
  resumo: 'Entenda o que muda.',
  imagem: 'https://exemplo.test/capa.jpg',
  categoria: { id: 2, nome: 'Tecnologia', slug: 'tecnologia', cor: '#1B48C4' },
  autor: { id: 3, nome: 'Beatriz Lima', username: 'beatriz' },
  visualizacoes: 1200,
  tempo_leitura: 4,
  data_publicacao: new Date().toISOString(),
  exclusivo: true,
}

describe('CartaoNoticia', () => {
  it('mostra título, categoria e autor', () => {
    render(
      <MemoryRouter>
        <CartaoNoticia noticia={noticia} />
      </MemoryRouter>
    )
    expect(screen.getByText(noticia.titulo)).toBeInTheDocument()
    expect(screen.getByText('Tecnologia')).toBeInTheDocument()
    expect(screen.getByText('Beatriz Lima')).toBeInTheDocument()
  })

  it('aponta para a página da matéria', () => {
    render(
      <MemoryRouter>
        <CartaoNoticia noticia={noticia} />
      </MemoryRouter>
    )
    const link = screen.getByLabelText(noticia.titulo)
    expect(link).toHaveAttribute('href', '/noticia/nova-politica-de-dados')
  })

  it('sinaliza conteúdo exclusivo', () => {
    render(
      <MemoryRouter>
        <CartaoNoticia noticia={noticia} />
      </MemoryRouter>
    )
    expect(screen.getByText('Exclusivo')).toBeInTheDocument()
  })
})
