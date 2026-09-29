import { act, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import CarrosselNoticias, { INTERVALO_AUTOPLAY } from '../components/CarrosselNoticias'
import HeroNoticias from '../components/HeroNoticias'

const categoria = { id: 1, nome: 'Economia', slug: 'economia', cor: '#1B48C4' }

function criarNoticia(id, extra = {}) {
  return {
    id,
    titulo: `Manchete ${id}`,
    slug: `manchete-${id}`,
    resumo: `Resumo da manchete ${id}`,
    imagem: `https://exemplo.test/capa-${id}.jpg`,
    categoria,
    autor: { id: 9, nome: 'Redação' },
    data_publicacao: new Date().toISOString(),
    origem: null,
    ...extra,
  }
}

const LISTA = [criarNoticia(1), criarNoticia(2), criarNoticia(3)]

// o jsdom não implementa matchMedia; `reduzir` simula "reduzir movimento" do sistema
function simularMatchMedia(reduzir = false) {
  window.matchMedia = vi.fn().mockImplementation((consulta) => ({
    matches: reduzir && consulta.includes('prefers-reduced-motion'),
    media: consulta,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
  }))
}

function renderizar(elemento) {
  return render(<MemoryRouter>{elemento}</MemoryRouter>)
}

const slideAtivo = (container) => container.querySelector('.carrossel__slide--ativo')

describe('CarrosselNoticias', () => {
  beforeEach(() => {
    simularMatchMedia(false)
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('mostra imagem, título, categoria e resumo e leva para a notícia', () => {
    const { container } = renderizar(<CarrosselNoticias noticias={LISTA} />)
    const ativo = slideAtivo(container)

    expect(ativo).toHaveTextContent('Manchete 1')
    expect(ativo).toHaveTextContent('Resumo da manchete 1')
    expect(ativo).toHaveTextContent('Economia')
    expect(ativo.querySelector('img')).toHaveAttribute('src', 'https://exemplo.test/capa-1.jpg')
    expect(ativo.querySelector('a')).toHaveAttribute('href', '/noticia/manchete-1')
    expect(screen.getByRole('region', { name: 'Manchetes' })).toHaveAttribute('aria-roledescription', 'carrossel')
  })

  it('credita a fonte original nas notícias importadas', () => {
    const importada = criarNoticia(7, { origem: { fonte: 'Agência Brasil', url: 'https://fonte.test/a' } })
    const { container } = renderizar(<CarrosselNoticias noticias={[importada]} />)
    expect(slideAtivo(container)).toHaveTextContent('Agência Brasil')
  })

  it('navega pelas setas, pelos pontos e pelo teclado', () => {
    const { container } = renderizar(<CarrosselNoticias noticias={LISTA} />)

    fireEvent.click(screen.getByRole('button', { name: 'Próxima notícia' }))
    expect(slideAtivo(container)).toHaveTextContent('Manchete 2')

    fireEvent.click(screen.getByRole('button', { name: 'Notícia anterior' }))
    expect(slideAtivo(container)).toHaveTextContent('Manchete 1')

    // volta do primeiro para o último
    fireEvent.click(screen.getByRole('button', { name: 'Notícia anterior' }))
    expect(slideAtivo(container)).toHaveTextContent('Manchete 3')

    fireEvent.click(screen.getByRole('button', { name: /Ir para a notícia 2/ }))
    expect(slideAtivo(container)).toHaveTextContent('Manchete 2')

    fireEvent.keyDown(screen.getByRole('region', { name: 'Manchetes' }), { key: 'ArrowRight' })
    expect(slideAtivo(container)).toHaveTextContent('Manchete 3')
  })

  it('esconde dos leitores de tela e do Tab os slides fora de vista', () => {
    const { container } = renderizar(<CarrosselNoticias noticias={LISTA} />)
    const slides = container.querySelectorAll('.carrossel__slide')
    expect(slides[0]).not.toHaveAttribute('aria-hidden')
    expect(slides[1]).toHaveAttribute('aria-hidden', 'true')
    expect(slides[1].querySelector('a')).toHaveAttribute('tabindex', '-1')
    expect(slides[0]).toHaveAttribute('aria-label', '1 de 3')
  })

  it('avança sozinho (autoplay) e para quando o leitor pausa', () => {
    const { container } = renderizar(<CarrosselNoticias noticias={LISTA} />)

    act(() => { vi.advanceTimersByTime(INTERVALO_AUTOPLAY) })
    expect(slideAtivo(container)).toHaveTextContent('Manchete 2')

    fireEvent.click(screen.getByRole('button', { name: /Pausar/ }))
    act(() => { vi.advanceTimersByTime(INTERVALO_AUTOPLAY * 3) })
    expect(slideAtivo(container)).toHaveTextContent('Manchete 2')

    fireEvent.click(screen.getByRole('button', { name: /Retomar/ }))
    act(() => { vi.advanceTimersByTime(INTERVALO_AUTOPLAY) })
    expect(slideAtivo(container)).toHaveTextContent('Manchete 3')
  })

  it('pausa com o mouse em cima', () => {
    const { container } = renderizar(<CarrosselNoticias noticias={LISTA} />)
    fireEvent.mouseEnter(screen.getByRole('region', { name: 'Manchetes' }))
    act(() => { vi.advanceTimersByTime(INTERVALO_AUTOPLAY * 2) })
    expect(slideAtivo(container)).toHaveTextContent('Manchete 1')

    fireEvent.mouseLeave(screen.getByRole('region', { name: 'Manchetes' }))
    act(() => { vi.advanceTimersByTime(INTERVALO_AUTOPLAY) })
    expect(slideAtivo(container)).toHaveTextContent('Manchete 2')
  })

  it('não troca sozinho para quem pediu menos movimento', () => {
    simularMatchMedia(true)
    const { container } = renderizar(<CarrosselNoticias noticias={LISTA} />)
    act(() => { vi.advanceTimersByTime(INTERVALO_AUTOPLAY * 3) })
    expect(slideAtivo(container)).toHaveTextContent('Manchete 1')
    expect(screen.getByRole('button', { name: /Retomar/ })).toBeInTheDocument()
  })

  it('continua na mesma notícia quando a lista é atualizada', () => {
    const { container, rerender } = renderizar(<CarrosselNoticias noticias={LISTA} />)
    fireEvent.click(screen.getByRole('button', { name: /Ir para a notícia 2/ }))
    expect(slideAtivo(container)).toHaveTextContent('Manchete 2')

    // chegou uma notícia importada nova no começo da lista
    const atualizada = [criarNoticia(10), ...LISTA]
    rerender(<MemoryRouter><CarrosselNoticias noticias={atualizada} /></MemoryRouter>)
    expect(slideAtivo(container)).toHaveTextContent('Manchete 2')
    expect(container.querySelectorAll('.carrossel__slide')).toHaveLength(4)
  })

  it('sem controles quando há uma notícia só', () => {
    renderizar(<CarrosselNoticias noticias={[criarNoticia(1)]} />)
    expect(screen.queryByRole('button', { name: 'Próxima notícia' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Pausar/ })).not.toBeInTheDocument()
  })

  it('mostra o esqueleto enquanto carrega', () => {
    renderizar(<CarrosselNoticias carregando />)
    expect(screen.getByLabelText('Carregando manchetes')).toHaveAttribute('aria-busy', 'true')
  })
})

describe('HeroNoticias', () => {
  beforeEach(() => simularMatchMedia(false))

  it('não repete na coluna "Em destaque" o que está no carrossel', () => {
    const secundarias = [criarNoticia(2), criarNoticia(4), criarNoticia(5)]
    const { container } = renderizar(
      <HeroNoticias carrossel={LISTA} principal={criarNoticia(1)} secundarias={secundarias} />
    )
    const lateral = container.querySelector('.hero__secundarias')
    expect(lateral).toHaveTextContent('Manchete 4')
    expect(lateral).toHaveTextContent('Manchete 5')
    expect(lateral).not.toHaveTextContent('Manchete 1')
    expect(lateral).not.toHaveTextContent('Manchete 2')
  })

  it('usa a manchete principal quando o carrossel vem vazio', () => {
    const { container } = renderizar(<HeroNoticias carrossel={[]} principal={criarNoticia(8)} secundarias={[]} />)
    expect(slideAtivo(container)).toHaveTextContent('Manchete 8')
    expect(container.querySelector('.hero')).toHaveClass('hero--unico')
  })

  it('não mostra nada sem notícias', () => {
    const { container } = renderizar(<HeroNoticias carrossel={[]} principal={null} secundarias={[]} />)
    expect(container.querySelector('.hero')).toBeNull()
  })
})
