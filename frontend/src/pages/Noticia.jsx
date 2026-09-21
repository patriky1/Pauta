import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import Anuncio from '../components/Anuncio'
import BotoesCompartilhar from '../components/BotoesCompartilhar'
import CartaoAutor from '../components/CartaoAutor'
import CartaoNoticia from '../components/CartaoNoticia'
import CategoriaSelo from '../components/CategoriaSelo'
import Icone from '../components/Icone'
import Imagem from '../components/Imagem'
import ListaComentarios from '../components/ListaComentarios'
import { EsqueletoMateria } from '../components/Esqueleto'
import { EstadoErro } from '../components/Estado'
import { useAuth } from '../contexts/AuthContext'
import { useAviso } from '../contexts/AvisoContext'
import useRequisicao from '../hooks/useRequisicao'
import useSeo from '../hooks/useSeo'
import { noticias as servico } from '../services/noticias'
import { social } from '../services/social'
import { URL_SITE } from '../utils/constantes'
import { dataCompleta, numero, tempoRelativo } from '../utils/formatar'

/** Aceita a resposta da API como objeto, lista ou página ({ results }). */
function normalizar(resposta) {
  if (!resposta) return null
  if (Array.isArray(resposta)) return resposta[0] || null
  if (Array.isArray(resposta.results)) return resposta.results[0] || null
  return resposta
}

function BarraProgresso() {
  const [progresso, setProgresso] = useState(0)

  useEffect(() => {
    let quadro = null
    const medir = () => {
      quadro = null
      const alvo = document.querySelector('.materia__corpo')
      if (!alvo) return
      const { top, height } = alvo.getBoundingClientRect()
      const lido = Math.min(Math.max((window.innerHeight * 0.4 - top) / height, 0), 1)
      setProgresso(lido * 100)
    }
    const agendar = () => { if (!quadro) quadro = requestAnimationFrame(medir) }
    window.addEventListener('scroll', agendar, { passive: true })
    window.addEventListener('resize', agendar)
    medir()
    return () => {
      window.removeEventListener('scroll', agendar)
      window.removeEventListener('resize', agendar)
      if (quadro) cancelAnimationFrame(quadro)
    }
  }, [])

  return <div className="materia__progresso" style={{ width: `${progresso}%` }} aria-hidden="true" />
}

export default function Noticia() {
  const { slug } = useParams()
  const { autenticado } = useAuth()
  const { mostrar } = useAviso()
  const [modoLeitura, setModoLeitura] = useState(false)
  const [favoritada, setFavoritada] = useState(false)
  const entrada = useRef(Date.now())

  const buscar = useCallback(() => servico.detalhe(slug), [slug])
  const { dados, carregando, erro, recarregar } = useRequisicao(buscar, [slug])
  const noticia = normalizar(dados)

  useEffect(() => { if (noticia) setFavoritada(Boolean(noticia.favoritada)) }, [noticia])

  useEffect(() => {
    document.body.classList.toggle('modo-leitura', modoLeitura)
    return () => document.body.classList.remove('modo-leitura')
  }, [modoLeitura])

  useEffect(() => { setModoLeitura(false) }, [slug])

  // registra quanto tempo o leitor passou na matéria
  useEffect(() => {
    entrada.current = Date.now()
    return () => {
      const segundos = Math.round((Date.now() - entrada.current) / 1000)
      if (slug && segundos > 5) servico.tempoLeitura(slug, segundos).catch(() => null)
    }
  }, [slug])

  useSeo({
    titulo: noticia?.titulo,
    descricao: noticia?.resumo,
    imagem: noticia?.imagem,
    caminho: noticia?.slug ? `/noticia/${noticia.slug}` : undefined,
    tipo: 'article',
    schema: noticia
      ? {
          '@context': 'https://schema.org',
          '@type': 'NewsArticle',
          headline: noticia.titulo || '',
          description: noticia.resumo || '',
          image: noticia.imagem ? [noticia.imagem] : undefined,
          datePublished: noticia.data_publicacao,
          dateModified: noticia.data_atualizacao || noticia.data_publicacao,
          articleSection: noticia.categoria?.nome || '',
          keywords: (noticia.tags || []).map((tag) => tag.nome).join(', '),
          author: { '@type': 'Person', name: noticia.autor?.nome || 'Redação' },
          publisher: { '@type': 'Organization', name: 'Pauta' },
          mainEntityOfPage: `${URL_SITE}/noticia/${noticia.slug}`,
        }
      : undefined,
  })

  const alternarFavorito = async () => {
    if (!autenticado) {
      mostrar('Entre na sua conta para salvar notícias.', 'erro')
      return
    }
    if (!noticia?.id) return
    try {
      const resposta = await social.alternarFavorito(noticia.id)
      setFavoritada(resposta.favoritada)
      mostrar(resposta.favoritada ? 'Salva em Notícias salvas.' : 'Removida dos salvos.')
    } catch {
      mostrar('Não foi possível atualizar os salvos.', 'erro')
    }
  }

  if (erro) {
    return <div className="container"><EstadoErro mensagem={erro} aoTentarNovamente={recarregar} /></div>
  }
  if (carregando) return <div className="container"><EsqueletoMateria /></div>
  if (!noticia) {
    return (
      <div className="container">
        <EstadoErro mensagem="Esta matéria não foi encontrada ou saiu do ar." />
      </div>
    )
  }

  return (
    <div className="container">
      <BarraProgresso />
      <article className="materia">
        <div className="cartao__selos">
          {noticia.categoria ? <CategoriaSelo categoria={noticia.categoria} /> : null}
          {noticia.breaking_news ? <span className="selo selo--exclusivo">Urgente</span> : null}
          {noticia.exclusivo ? <span className="selo selo--exclusivo">Exclusivo</span> : null}
        </div>
        <h1 className="materia__titulo">{noticia.titulo}</h1>
        {noticia.subtitulo ? <p className="materia__linha-fina">{noticia.subtitulo}</p> : null}

        <div className="materia__assinatura">
          {noticia.autor ? <CartaoAutor autor={noticia.autor} compacto /> : null}
          <div className="materia__datas">
            {noticia.data_publicacao ? (
              <div>
                <time dateTime={noticia.data_publicacao}>Publicado em {dataCompleta(noticia.data_publicacao)}</time>
              </div>
            ) : null}
            {noticia.data_atualizacao ? <div>Atualizado {tempoRelativo(noticia.data_atualizacao)}</div> : null}
            <div>
              {noticia.tempo_leitura || 1} min de leitura · {numero(noticia.visualizacoes || 0)} leituras
            </div>
          </div>
        </div>

        <div className="materia__barra">
          <button type="button" className="botao" onClick={() => setModoLeitura((v) => !v)} aria-pressed={modoLeitura}>
            <Icone nome="leitura" tamanho={16} /> {modoLeitura ? 'Sair do modo leitura' : 'Modo leitura'}
          </button>
          <button type="button" className="botao" onClick={alternarFavorito} aria-pressed={favoritada}>
            <Icone nome={favoritada ? 'marcador' : 'marcadorVazio'} tamanho={16} />
            {favoritada ? 'Salva' : 'Salvar'}
          </button>
          <a href="#comentarios" className="botao">
            <Icone nome="comentario" tamanho={16} preenchido={false} /> {noticia.total_comentarios || 0}
            <span className="so-desktop" style={{ display: 'inline' }}>comentários</span>
          </a>
        </div>

        {noticia.cobertura_ao_vivo ? (
          <p className="aviso">
            Esta pauta tem cobertura ao vivo.{' '}
            <Link to={`/ao-vivo/${noticia.cobertura_ao_vivo.slug}`}>Acompanhe minuto a minuto</Link>.
          </p>
        ) : null}

        {noticia.imagem ? (
          <figure className="materia__figura">
            <Imagem src={noticia.imagem} alt={noticia.imagem_legenda || ''} largura={1200} altura={750} prioridade />
            {noticia.imagem_legenda || noticia.imagem_credito ? (
              <figcaption>
                {noticia.imagem_legenda}
                {noticia.imagem_credito ? ` — ${noticia.imagem_credito}` : ''}
              </figcaption>
            ) : null}
          </figure>
        ) : null}

        {/* o conteúdo vem da redação, escrito no editor do painel */}
        <div className="materia__corpo" dangerouslySetInnerHTML={{ __html: noticia.conteudo || '' }} />

        {noticia.midias?.length ? (
          <section className="secao">
            <h2 className="secao__titulo secao__titulo--pequeno" style={{ marginBottom: 'var(--e-3)' }}>Multimídia</h2>
            <div className="grade grade--manter">
              {noticia.midias.map((midia) => (
                <figure key={midia.id} style={{ margin: 0 }}>
                  {midia.tipo === 'VIDEO' ? (
                    <video controls src={midia.arquivo_url || midia.url} style={{ width: '100%', borderRadius: 12 }} />
                  ) : midia.tipo === 'AUDIO' || midia.tipo === 'PODCAST' ? (
                    <audio controls src={midia.arquivo_url || midia.url} style={{ width: '100%' }} />
                  ) : (
                    <Imagem src={midia.arquivo_url || midia.url} alt={midia.legenda || ''} estilo={{ aspectRatio: '4 / 3' }} />
                  )}
                  {midia.legenda ? <figcaption className="cartao__meta" style={{ marginTop: 6 }}>{midia.legenda}</figcaption> : null}
                </figure>
              ))}
            </div>
          </section>
        ) : null}

        {noticia.fontes?.length ? (
          <section className="materia__fontes">
            <h2 style={{ fontSize: 'var(--t-lg)', marginBottom: 8 }}>Fontes desta matéria</h2>
            <ul>
              {noticia.fontes.map((fonte) => (
                <li key={fonte.id}>
                  {fonte.url ? (
                    <a href={fonte.url} target="_blank" rel="noopener noreferrer">{fonte.titulo}</a>
                  ) : (
                    fonte.titulo
                  )}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {noticia.tags?.length ? (
          <div className="materia__barra">
            {noticia.tags.map((tag) => (
              <Link key={tag.id} to={`/busca?tag=${tag.slug}`} className="selo selo--linha">
                #{tag.nome}
              </Link>
            ))}
          </div>
        ) : null}

        <BotoesCompartilhar noticia={noticia} />

        <Anuncio posicao="MATERIA" />

        <ListaComentarios noticia={noticia} />
      </article>

      {noticia.relacionadas?.length ? (
        <section className="secao relacionadas">
          <div className="secao__cabecalho">
            <h2 className="secao__titulo">Leia também</h2>
            {noticia.categoria ? (
              <Link to={`/categoria/${noticia.categoria.slug}`} className="secao__link">
                Mais de {noticia.categoria.nome}
              </Link>
            ) : null}
          </div>
          <div className="grade">
            {noticia.relacionadas.map((item) => (
              <CartaoNoticia key={item.id} noticia={item} />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  )
}
