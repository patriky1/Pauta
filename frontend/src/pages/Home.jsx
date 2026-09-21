import { useCallback, useState } from 'react'
import { Link } from 'react-router-dom'

import AbasFeed from '../components/AbasFeed'
import Anuncio from '../components/Anuncio'
import CartaoNoticia from '../components/CartaoNoticia'
import GradeNoticias from '../components/GradeNoticias'
import HeroNoticias from '../components/HeroNoticias'
import ListaTendencias from '../components/ListaTendencias'
import Paginacao from '../components/Paginacao'
import { useAuth } from '../contexts/AuthContext'
import useListaPaginada from '../hooks/useListaPaginada'
import useRequisicao from '../hooks/useRequisicao'
import useSeo from '../hooks/useSeo'
import { catalogo, noticias as servico } from '../services/noticias'
import { ABAS_FEED } from '../utils/constantes'

const BUSCADORES = {
  'para-voce': (pagina) => servico.paraVoce({ page: pagina }),
  ultimas: (pagina) => servico.ultimas({ page: pagina }),
  'mais-lidas': (pagina) => servico.maisLidas('semana', { page: pagina }),
  tendencias: (pagina) => servico.listar({ page: pagina, ordering: '-visualizacoes' }),
  seguindo: (pagina) => servico.seguindo({ page: pagina }),
}

export default function Home() {
  const { autenticado } = useAuth()
  const [aba, setAba] = useState('para-voce')

  useSeo({
    descricao: 'Notícias em tempo real com feed personalizado, cobertura ao vivo e leitura sem ruído.',
    caminho: '/',
  })

  const { dados: destaques, carregando: carregandoHero } = useRequisicao(() => servico.destaques(), [])
  const { dados: tendencias } = useRequisicao(() => catalogo.tendencias(), [])
  const { dados: maisLidas } = useRequisicao(() => servico.maisLidas('hoje', { page_size: 5 }), [])

  const buscar = useCallback((pagina) => BUSCADORES[aba](pagina), [aba])
  const feed = useListaPaginada(buscar, [aba])

  const abas = autenticado ? ABAS_FEED : ABAS_FEED.filter((item) => item.chave !== 'seguindo')
  const listaMaisLidas = maisLidas?.results || []

  return (
    <div className="container">
      <HeroNoticias
        principal={destaques?.principal}
        secundarias={destaques?.secundarias || []}
        carregando={carregandoHero}
      />

      <Anuncio posicao="TOPO" />

      <div className="coluna-dupla secao">
        <div style={{ minWidth: 0 }}>
          <div className="secao__cabecalho" style={{ marginBottom: 'var(--e-2)' }}>
            <h2 className="secao__titulo">Seu feed</h2>
            {autenticado ? (
              <Link to="/interesses" className="secao__link">Ajustar interesses</Link>
            ) : (
              <Link to="/cadastrar" className="secao__link">Personalize com uma conta grátis</Link>
            )}
          </div>

          <AbasFeed abas={abas} ativa={aba} aoTrocar={setAba} />

          <GradeNoticias
            noticias={feed.itens}
            carregando={feed.carregando}
            erro={feed.erro}
            aoRecarregar={feed.recarregar}
            vazioTitulo={aba === 'seguindo' ? 'Você ainda não segue nada' : 'Sem notícias aqui'}
            vazioDescricao={
              aba === 'seguindo'
                ? 'Siga editorias, autores e assuntos para montar o seu feed.'
                : 'Volte em instantes: a redação publica ao longo de todo o dia.'
            }
            vazioAcao={
              aba === 'seguindo' ? <Link to="/interesses" className="botao botao--primario">Escolher interesses</Link> : null
            }
          />
          <Paginacao
            pagina={feed.pagina}
            temMais={feed.temMais}
            carregando={feed.carregando}
            total={feed.total}
            aoCarregarMais={feed.carregarMais}
          />
        </div>

        <aside className="lateral" aria-label="Destaques laterais">
          <ListaTendencias assuntos={tendencias?.categorias || []} />

          {listaMaisLidas.length ? (
            <section>
              <div className="secao__cabecalho" style={{ marginBottom: 'var(--e-3)' }}>
                <h2 className="secao__titulo secao__titulo--pequeno">Mais lidas hoje</h2>
                <Link className="secao__link" to="/mais-lidas">Ver ranking</Link>
              </div>
              <div className="lista-ranking">
                {listaMaisLidas.map((noticia) => (
                  <CartaoNoticia key={noticia.id} noticia={noticia} variante="horizontal" />
                ))}
              </div>
            </section>
          ) : null}

          <Anuncio posicao="LATERAL" />
        </aside>
      </div>
    </div>
  )
}
