import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { Link, NavLink, useLocation } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext'
import useRequisicao from '../hooks/useRequisicao'
import { catalogo } from '../services/noticias'
import BarraBusca from './BarraBusca'
import BotaoTema from './BotaoTema'
import Icone from './Icone'
import MenuUsuario from './MenuUsuario'
import SinoNotificacoes from './SinoNotificacoes'

const SECOES = [
  { para: '/', rotulo: 'Início', fim: true },
  { para: '/ao-vivo', rotulo: 'Ao vivo', aoVivo: true },
  { para: '/tendencias', rotulo: 'Tendências' },
  { para: '/mais-lidas', rotulo: 'Mais lidas' },
  { para: '/videos', rotulo: 'Vídeos' },
]

export default function Cabecalho() {
  const { autenticado, ehRedacao, sair } = useAuth()
  const [gaveta, setGaveta] = useState(false)
  const [buscaAberta, setBuscaAberta] = useState(false)
  const local = useLocation()
  const { dados: categorias } = useRequisicao(() => catalogo.categorias(), [])

  useEffect(() => {
    setGaveta(false)
    setBuscaAberta(false)
  }, [local.pathname, local.search])

  // trava a rolagem do fundo enquanto a gaveta está aberta
  useEffect(() => {
    if (!gaveta) return undefined
    const anterior = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const tecla = (evento) => { if (evento.key === 'Escape') setGaveta(false) }
    document.addEventListener('keydown', tecla)
    return () => {
      document.body.style.overflow = anterior
      document.removeEventListener('keydown', tecla)
    }
  }, [gaveta])

  const listaCategorias = Array.isArray(categorias) ? categorias : categorias?.results || []

  return (
    <header className="cabecalho">
      <div className="container">
        <div className="cabecalho__linha">
          <Link to="/" className="marca" aria-label="Pauta, página inicial">
            Pauta<span className="marca__ponto" aria-hidden="true" />
          </Link>

          <div className="cabecalho__busca">
            <BarraBusca />
          </div>

          <div className="cabecalho__acoes">
            <button
              type="button"
              className="icone-botao so-movel"
              onClick={() => setBuscaAberta((v) => !v)}
              aria-label={buscaAberta ? 'Fechar busca' : 'Buscar'}
              aria-expanded={buscaAberta}
            >
              <Icone nome={buscaAberta ? 'fechar' : 'busca'} tamanho={19} />
            </button>
            <BotaoTema />
            <SinoNotificacoes />
            {autenticado ? (
              <span className="so-desktop" style={{ display: 'inline-flex' }}>
                <MenuUsuario />
              </span>
            ) : (
              <Link to="/entrar" className="botao botao--primario cabecalho__entrar">Entrar</Link>
            )}
            <button
              type="button"
              className="icone-botao so-movel"
              onClick={() => setGaveta(true)}
              aria-label="Abrir menu"
              aria-expanded={gaveta}
            >
              <Icone nome="menu" tamanho={20} />
            </button>
          </div>
        </div>

        <div className={`busca-movel${buscaAberta ? ' aberta' : ''}`}>
          {buscaAberta ? <BarraBusca autoFoco aoNavegar={() => setBuscaAberta(false)} /> : null}
        </div>

        <nav className="cabecalho__secoes" aria-label="Seções e editorias">
          {SECOES.map((secao) => (
            <NavLink
              key={secao.para}
              to={secao.para}
              end={secao.fim}
              className={({ isActive }) => `secao-principal${isActive ? ' ativo' : ''}`}
            >
              {secao.aoVivo ? <span className="ao-vivo-ponto" aria-hidden="true" /> : null}
              {secao.rotulo}
            </NavLink>
          ))}
          {listaCategorias.length ? <span className="cabecalho__divisor" aria-hidden="true" /> : null}
          {listaCategorias.map((categoria) => (
            <NavLink
              key={categoria.id}
              to={`/categoria/${categoria.slug}`}
              className={({ isActive }) => (isActive ? 'ativo' : undefined)}
            >
              {categoria.nome}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* portal: o backdrop-filter do cabeçalho prenderia o position: fixed da gaveta */}
      {gaveta ? createPortal(
        <div className="gaveta" role="dialog" aria-modal="true" aria-label="Menu">
          <button type="button" className="gaveta__fundo" aria-label="Fechar menu" onClick={() => setGaveta(false)} />
          <div className="gaveta__painel">
            <div className="gaveta__topo">
              <span className="marca">Pauta<span className="marca__ponto" aria-hidden="true" /></span>
              <button type="button" className="icone-botao" onClick={() => setGaveta(false)} aria-label="Fechar menu">
                <Icone nome="fechar" tamanho={18} />
              </button>
            </div>

            <div className="gaveta__grupo">
              <h4>Navegue</h4>
              {SECOES.map((secao) => (
                <NavLink key={secao.para} to={secao.para} end={secao.fim}>
                  {secao.rotulo}
                </NavLink>
              ))}
            </div>

            {listaCategorias.length ? (
              <div className="gaveta__grupo">
                <h4>Editorias</h4>
                <div className="gaveta__categorias">
                  {listaCategorias.map((categoria) => (
                    <Link key={categoria.id} to={`/categoria/${categoria.slug}`}>{categoria.nome}</Link>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="gaveta__grupo">
              <h4>Sua conta</h4>
              {autenticado ? (
                <>
                  <NavLink to="/perfil">Meu perfil</NavLink>
                  <NavLink to="/meus-favoritos">Notícias salvas</NavLink>
                  <NavLink to="/historico">Histórico</NavLink>
                  <NavLink to="/interesses">Meus interesses</NavLink>
                  {ehRedacao ? <NavLink to="/admin">Painel da redação</NavLink> : null}
                </>
              ) : (
                <>
                  <NavLink to="/entrar">Entrar</NavLink>
                  <NavLink to="/cadastrar">Criar conta</NavLink>
                </>
              )}
            </div>

            {autenticado ? (
              <button type="button" className="botao botao--contorno-perigo botao--bloco" onClick={sair}>
                Sair da conta
              </button>
            ) : null}
          </div>
        </div>,
        document.body
      ) : null}
    </header>
  )
}
