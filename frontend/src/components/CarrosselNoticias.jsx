import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import useMidia from '../hooks/useMidia'
import { tempoRelativo } from '../utils/formatar'
import CategoriaSelo from './CategoriaSelo'
import { Esqueleto } from './Esqueleto'
import Icone from './Icone'
import Imagem from './Imagem'

export const INTERVALO_AUTOPLAY = 6000
const DISTANCIA_MINIMA_ARRASTE = 50

/**
 * Carrossel das manchetes da home.
 *
 * - Autoplay a cada 6 s, com botão de pausa. Pausa sozinho com o mouse em cima,
 *   com o foco do teclado dentro dele e com a aba em segundo plano.
 * - Quem pediu "reduzir movimento" no sistema começa com o autoplay desligado.
 * - Navegação por setas, pontos, teclado (← →) e arraste no celular.
 * - Quando a lista é atualizada (nova importação), continua no mesmo slide.
 */
export default function CarrosselNoticias({ noticias = [], carregando = false, rotulo = 'Manchetes' }) {
  const reduzirMovimento = useMidia('(prefers-reduced-motion: reduce)')
  const total = noticias.length

  const [indice, setIndice] = useState(0)
  const [pausadoPeloUsuario, setPausadoPeloUsuario] = useState(reduzirMovimento)
  const [sobMouse, setSobMouse] = useState(false)
  const [comFoco, setComFoco] = useState(false)
  const [abaOculta, setAbaOculta] = useState(
    typeof document !== 'undefined' ? document.hidden : false
  )
  const [arraste, setArraste] = useState(0)
  // slides cuja imagem já pode ser baixada (atual + vizinhos + já vistos)
  const [liberadas, setLiberadas] = useState(() => new Set())

  const idAtual = useRef(null)
  const toque = useRef(null)
  const houveArraste = useRef(false)

  const atual = total ? Math.min(indice, total - 1) : 0
  const autoplay = total > 1 && !pausadoPeloUsuario && !sobMouse && !comFoco && !abaOculta

  useEffect(() => {
    if (reduzirMovimento) setPausadoPeloUsuario(true)
  }, [reduzirMovimento])

  // lista nova (ex.: notícias importadas agora): permanece na mesma notícia
  useEffect(() => {
    if (!total) return
    const posicao = noticias.findIndex((noticia) => noticia.id === idAtual.current)
    setIndice(posicao >= 0 ? posicao : 0)
  }, [noticias, total])

  useEffect(() => {
    idAtual.current = noticias[atual]?.id ?? null
    if (!total) return
    setLiberadas((anteriores) => {
      const ids = [atual, (atual + 1) % total, (atual - 1 + total) % total].map((i) => noticias[i]?.id)
      if (ids.every((id) => anteriores.has(id))) return anteriores
      const proximas = new Set(anteriores)
      ids.forEach((id) => proximas.add(id))
      return proximas
    })
  }, [atual, noticias, total])

  useEffect(() => {
    const aoMudarVisibilidade = () => setAbaOculta(document.hidden)
    document.addEventListener('visibilitychange', aoMudarVisibilidade)
    return () => document.removeEventListener('visibilitychange', aoMudarVisibilidade)
  }, [])

  const irPara = useCallback(
    (destino) => {
      if (!total) return
      setIndice(((destino % total) + total) % total)
    },
    [total]
  )
  const proximo = useCallback(() => irPara(atual + 1), [irPara, atual])
  const anterior = useCallback(() => irPara(atual - 1), [irPara, atual])

  // o tempo recomeça a cada troca de slide e a cada retomada
  useEffect(() => {
    if (!autoplay) return undefined
    const id = setTimeout(proximo, INTERVALO_AUTOPLAY)
    return () => clearTimeout(id)
  }, [autoplay, atual, proximo])

  const aoTeclar = (evento) => {
    if (evento.key === 'ArrowRight') {
      evento.preventDefault()
      proximo()
    } else if (evento.key === 'ArrowLeft') {
      evento.preventDefault()
      anterior()
    }
  }

  // só o foco do teclado pausa: um clique nas setas não deve travar o autoplay
  const aoReceberFoco = (evento) => {
    let peloTeclado = true
    try {
      peloTeclado = evento.target.matches(':focus-visible')
    } catch {
      peloTeclado = true
    }
    if (peloTeclado) setComFoco(true)
  }

  const aoPerderFoco = (evento) => {
    if (!evento.currentTarget.contains(evento.relatedTarget)) setComFoco(false)
  }

  // ---- arraste (toque e caneta; o mouse usa as setas) ----
  const aoIniciarArraste = (evento) => {
    if (evento.pointerType === 'mouse' || total < 2) return
    toque.current = { x: evento.clientX, y: evento.clientY, horizontal: null }
    houveArraste.current = false
  }
  const aoArrastar = (evento) => {
    const inicio = toque.current
    if (!inicio) return
    const dx = evento.clientX - inicio.x
    const dy = evento.clientY - inicio.y
    if (inicio.horizontal === null && (Math.abs(dx) > 8 || Math.abs(dy) > 8)) {
      inicio.horizontal = Math.abs(dx) > Math.abs(dy)
    }
    if (inicio.horizontal) setArraste(dx)
  }
  const aoSoltar = (evento) => {
    const inicio = toque.current
    toque.current = null
    if (!inicio) return
    const dx = evento.clientX - inicio.x
    setArraste(0)
    if (inicio.horizontal && Math.abs(dx) >= DISTANCIA_MINIMA_ARRASTE) {
      houveArraste.current = true
      if (dx < 0) proximo()
      else anterior()
    }
  }
  const aoCancelarArraste = () => {
    toque.current = null
    setArraste(0)
  }
  // um arraste não deve abrir a notícia que estava embaixo do dedo
  const aoClicarCaptura = (evento) => {
    if (houveArraste.current) {
      evento.preventDefault()
      evento.stopPropagation()
      houveArraste.current = false
    }
  }

  if (carregando && !total) {
    return (
      <div className="carrossel carrossel--carregando" aria-busy="true" aria-label="Carregando manchetes">
        <Esqueleto altura={0} estilo={{ aspectRatio: '16 / 10', borderRadius: 12 }} />
        <div className="carrossel__texto">
          <Esqueleto altura={14} largura="25%" />
          <div style={{ height: 12 }} />
          <Esqueleto altura={36} />
          <div style={{ height: 8 }} />
          <Esqueleto altura={36} largura="70%" />
        </div>
      </div>
    )
  }

  if (!total) return null

  const deslocamento = arraste ? `calc(${-atual * 100}% + ${arraste}px)` : `${-atual * 100}%`

  return (
    <section
      className="carrossel"
      aria-roledescription="carrossel"
      aria-label={rotulo}
      onKeyDown={aoTeclar}
      onMouseEnter={() => setSobMouse(true)}
      onMouseLeave={() => setSobMouse(false)}
      onFocus={aoReceberFoco}
      onBlur={aoPerderFoco}
    >
      <div
        className="carrossel__janela"
        onPointerDown={aoIniciarArraste}
        onPointerMove={aoArrastar}
        onPointerUp={aoSoltar}
        onPointerCancel={aoCancelarArraste}
        onClickCapture={aoClicarCaptura}
      >
        <div
          className={`carrossel__trilho${arraste ? ' carrossel__trilho--arrastando' : ''}`}
          style={{ transform: `translate3d(${deslocamento}, 0, 0)` }}
          aria-live={autoplay ? 'off' : 'polite'}
        >
          {noticias.map((noticia, posicao) => {
            const ativo = posicao === atual
            const carregar = posicao === 0 || liberadas.has(noticia.id)
            return (
              <div
                key={noticia.id}
                className={`carrossel__slide${ativo ? ' carrossel__slide--ativo' : ''}`}
                role="group"
                aria-roledescription="slide"
                aria-label={`${posicao + 1} de ${total}`}
                aria-hidden={ativo ? undefined : 'true'}
              >
                <Link
                  to={`/noticia/${noticia.slug}`}
                  className="carrossel__link"
                  tabIndex={ativo ? undefined : -1}
                  draggable="false"
                >
                  <Imagem
                    src={carregar ? noticia.imagem : null}
                    alt={noticia.imagem_legenda || ''}
                    largura={1200}
                    altura={750}
                    prioridade={posicao === 0}
                    carregamento={carregar ? 'eager' : 'lazy'}
                    key={carregar ? 'imagem' : 'reserva'}
                  />
                  <div className="carrossel__texto">
                    <div className="cartao__selos">
                      <CategoriaSelo categoria={noticia.categoria} link={false} />
                      {noticia.breaking_news ? <span className="selo selo--exclusivo">Urgente</span> : null}
                      {noticia.exclusivo ? <span className="selo selo--exclusivo">Exclusivo</span> : null}
                    </div>
                    <h2 className="carrossel__titulo">{noticia.titulo}</h2>
                    {noticia.resumo || noticia.subtitulo ? (
                      <p className="carrossel__resumo">{noticia.resumo || noticia.subtitulo}</p>
                    ) : null}
                    <div className="cartao__meta">
                      {noticia.origem?.fonte ? (
                        <>
                          <span>{noticia.origem.fonte}</span>
                          <span aria-hidden="true">·</span>
                        </>
                      ) : noticia.autor?.nome ? (
                        <>
                          <span>{noticia.autor.nome}</span>
                          <span aria-hidden="true">·</span>
                        </>
                      ) : null}
                      <time dateTime={noticia.data_publicacao}>{tempoRelativo(noticia.data_publicacao)}</time>
                    </div>
                  </div>
                </Link>
              </div>
            )
          })}
        </div>

        {total > 1 ? (
          <div className="carrossel__setas">
            <button type="button" className="carrossel__seta carrossel__seta--anterior" onClick={anterior} aria-label="Notícia anterior">
              <Icone nome="seta" tamanho={20} />
            </button>
            <button type="button" className="carrossel__seta" onClick={proximo} aria-label="Próxima notícia">
              <Icone nome="seta" tamanho={20} />
            </button>
          </div>
        ) : null}
      </div>

      {total > 1 ? (
        <div className="carrossel__controles">
          <button
            type="button"
            className="carrossel__pausa"
            onClick={() => setPausadoPeloUsuario((valor) => !valor)}
            aria-label={pausadoPeloUsuario ? 'Retomar a troca automática' : 'Pausar a troca automática'}
          >
            <Icone nome={pausadoPeloUsuario ? 'reproduzir' : 'pausar'} tamanho={14} />
          </button>
          <div className="carrossel__pontos">
            {noticias.map((noticia, posicao) => (
              <button
                key={noticia.id}
                type="button"
                className={`carrossel__ponto${posicao === atual ? ' carrossel__ponto--ativo' : ''}`}
                onClick={() => irPara(posicao)}
                aria-label={`Ir para a notícia ${posicao + 1}: ${noticia.titulo}`}
                aria-current={posicao === atual ? 'true' : undefined}
              >
                {posicao === atual && autoplay && !reduzirMovimento ? (
                  <span
                    className="carrossel__progresso"
                    key={`${atual}-${noticia.id}`}
                    style={{ animationDuration: `${INTERVALO_AUTOPLAY}ms` }}
                  />
                ) : null}
              </button>
            ))}
          </div>
          <span className="carrossel__contador" aria-hidden="true">
            {atual + 1}/{total}
          </span>
        </div>
      ) : null}
    </section>
  )
}
