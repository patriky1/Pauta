import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import CartaoAutor from '../components/CartaoAutor'
import GradeNoticias from '../components/GradeNoticias'
import { EstadoVazio } from '../components/Estado'
import useDebounce from '../hooks/useDebounce'
import useRequisicao from '../hooks/useRequisicao'
import useSeo from '../hooks/useSeo'
import { catalogo } from '../services/noticias'

export default function Busca() {
  const [parametros, setParametros] = useSearchParams()
  const qUrl = parametros.get('q') || ''
  const [termo, setTermo] = useState(qUrl)
  const termoAtrasado = useDebounce(termo, 400)
  const ultimoEscrito = useRef(qUrl)

  const filtros = {
    categoria: parametros.get('categoria') || '',
    tag: parametros.get('tag') || '',
    desde: parametros.get('desde') || '',
    ate: parametros.get('ate') || '',
  }

  // mudança vinda de fora (ex.: busca do cabeçalho) atualiza o campo
  useEffect(() => {
    if (qUrl !== ultimoEscrito.current) {
      ultimoEscrito.current = qUrl
      setTermo(qUrl)
    }
  }, [qUrl])

  // o que o usuário digita vai para a URL (compartilhável)
  useEffect(() => {
    const texto = termoAtrasado.trim()
    if (texto === ultimoEscrito.current) return
    ultimoEscrito.current = texto
    const atuais = new URLSearchParams(parametros)
    if (texto) atuais.set('q', texto)
    else atuais.delete('q')
    setParametros(atuais, { replace: true })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [termoAtrasado])

  const { dados: categoriasDados } = useRequisicao(() => catalogo.categorias(), [])
  const categorias = Array.isArray(categoriasDados) ? categoriasDados : categoriasDados?.results || []

  const consulta = qUrl.trim().length >= 2 ? qUrl.trim() : filtros.tag
  const chave = [consulta, filtros.categoria, filtros.tag, filtros.desde, filtros.ate].join('|')

  const buscar = useCallback(
    () =>
      catalogo.buscar({
        q: consulta,
        categoria: filtros.categoria || undefined,
        tag: filtros.tag || undefined,
        desde: filtros.desde || undefined,
        ate: filtros.ate || undefined,
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [chave]
  )
  const { dados, carregando, erro, recarregar } = useRequisicao(buscar, [chave], { ativo: Boolean(consulta) })

  useSeo({ titulo: consulta ? `Busca: ${consulta}` : 'Busca', caminho: '/busca' })

  const trocarFiltro = (campo, valor) => {
    const atuais = new URLSearchParams(parametros)
    if (valor) atuais.set(campo, valor)
    else atuais.delete(campo)
    setParametros(atuais)
  }

  const limparFiltros = () => {
    const atuais = new URLSearchParams()
    if (qUrl) atuais.set('q', qUrl)
    setParametros(atuais)
  }

  const temFiltro = filtros.categoria || filtros.tag || filtros.desde || filtros.ate

  return (
    <div className="container pagina">
      <header className="pagina__cabecalho">
        <h1 className="titulo-pagina">Busca</h1>
      </header>

      <div className="bloco" style={{ marginBottom: 'var(--e-4)' }}>
        <div className="campo">
          <label htmlFor="busca-principal">O que você procura?</label>
          <input
            id="busca-principal"
            type="search"
            value={termo}
            onChange={(evento) => setTermo(evento.target.value)}
            placeholder="Palavra-chave, autor ou assunto"
            enterKeyHint="search"
          />
        </div>

        <div className="filtros">
          <div className="campo">
            <label htmlFor="filtro-categoria">Editoria</label>
            <select id="filtro-categoria" value={filtros.categoria} onChange={(e) => trocarFiltro('categoria', e.target.value)}>
              <option value="">Todas</option>
              {categorias.map((categoria) => (
                <option key={categoria.id} value={categoria.slug}>{categoria.nome}</option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="filtro-tag">Tag</label>
            <input id="filtro-tag" value={filtros.tag} onChange={(e) => trocarFiltro('tag', e.target.value)} placeholder="ex.: eleicoes" />
          </div>
          <div className="campo">
            <label htmlFor="filtro-desde">De</label>
            <input id="filtro-desde" type="date" value={filtros.desde} onChange={(e) => trocarFiltro('desde', e.target.value)} />
          </div>
          <div className="campo">
            <label htmlFor="filtro-ate">Até</label>
            <input id="filtro-ate" type="date" value={filtros.ate} onChange={(e) => trocarFiltro('ate', e.target.value)} />
          </div>
        </div>
        {temFiltro ? (
          <button type="button" className="botao botao--fantasma botao--pequeno" onClick={limparFiltros}>
            Limpar filtros
          </button>
        ) : null}
      </div>

      {!consulta ? (
        <EstadoVazio
          icone="busca"
          titulo="Comece digitando"
          descricao="Digite ao menos duas letras para buscar entre todas as matérias publicadas."
        />
      ) : (
        <>
          <p style={{ color: 'var(--grafite)' }} aria-live="polite">
            {carregando
              ? 'Buscando…'
              : `${dados?.total ?? 0} ${dados?.total === 1 ? 'matéria encontrada' : 'matérias encontradas'} para “${consulta}”`}
          </p>

          {dados?.autores?.length ? (
            <section style={{ margin: 'var(--e-4) 0' }}>
              <h2 className="secao__titulo secao__titulo--pequeno" style={{ marginBottom: 'var(--e-3)' }}>Autores</h2>
              <div className="grade grade--2 grade--manter">
                {dados.autores.map((autor) => (
                  <div key={autor.id} className="bloco"><CartaoAutor autor={autor} compacto /></div>
                ))}
              </div>
            </section>
          ) : null}

          {dados?.tags?.length ? (
            <div className="materia__barra">
              {dados.tags.map((tag) => (
                <Link key={tag.id} to={`/busca?tag=${tag.slug}`} className="selo selo--linha">#{tag.nome}</Link>
              ))}
            </div>
          ) : null}

          <GradeNoticias
            noticias={dados?.noticias || []}
            carregando={carregando}
            erro={erro}
            aoRecarregar={recarregar}
            vazioTitulo="Nenhuma matéria encontrada"
            vazioDescricao="Tente outras palavras ou remova os filtros."
          />
        </>
      )}
    </div>
  )
}
