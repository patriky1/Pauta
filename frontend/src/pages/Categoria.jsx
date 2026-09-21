import { useState } from 'react'
import { useParams } from 'react-router-dom'

import GradeNoticias from '../components/GradeNoticias'
import Paginacao from '../components/Paginacao'
import { useAuth } from '../contexts/AuthContext'
import { useAviso } from '../contexts/AvisoContext'
import useListaPaginada from '../hooks/useListaPaginada'
import useRequisicao from '../hooks/useRequisicao'
import useSeo from '../hooks/useSeo'
import { catalogo, noticias as servico } from '../services/noticias'
import { social } from '../services/social'

export default function Categoria() {
  const { slug } = useParams()
  const { autenticado } = useAuth()
  const { mostrar } = useAviso()
  const [seguindo, setSeguindo] = useState(null)

  const { dados: categoria, erro: erroCategoria } = useRequisicao(() => catalogo.categoria(slug), [slug])
  const lista = useListaPaginada((pagina) => servico.listar({ categoria: slug, page: pagina }), [slug])

  useSeo({
    titulo: categoria?.nome,
    descricao: categoria?.descricao || `Últimas notícias de ${categoria?.nome || ''}.`,
    caminho: `/categoria/${slug}`,
  })

  const estaSeguindo = seguindo === null ? Boolean(categoria?.seguindo) : seguindo
  const nome = categoria?.nome || (erroCategoria ? 'Editoria' : '…')

  const alternar = async () => {
    if (!autenticado) { mostrar('Entre na sua conta para seguir esta editoria.', 'erro'); return }
    try {
      const resposta = await social.alternarSeguir('categories', slug)
      setSeguindo(resposta.seguindo)
      mostrar(resposta.seguindo ? `Você agora segue ${nome}.` : `Deixou de seguir ${nome}.`)
    } catch {
      mostrar('Não foi possível atualizar agora.', 'erro')
    }
  }

  return (
    <div className="container pagina">
      <header className="pagina__cabecalho" style={{ borderLeft: `4px solid ${categoria?.cor || 'var(--acento)'}`, paddingLeft: 16 }}>
        <div>
          <h1 className="titulo-pagina">{nome}</h1>
          {categoria?.descricao ? <p className="pagina__descricao">{categoria.descricao}</p> : null}
        </div>
        <button
          type="button"
          className={`botao${estaSeguindo ? '' : ' botao--primario'}`}
          onClick={alternar}
          aria-pressed={estaSeguindo}
        >
          {estaSeguindo ? 'Seguindo' : 'Seguir editoria'}
        </button>
      </header>

      <GradeNoticias
        noticias={lista.itens}
        carregando={lista.carregando}
        erro={lista.erro}
        aoRecarregar={lista.recarregar}
        vazioTitulo="Ainda não há matérias nesta editoria"
      />
      <Paginacao
        pagina={lista.pagina}
        temMais={lista.temMais}
        carregando={lista.carregando}
        total={lista.total}
        aoCarregarMais={lista.carregarMais}
      />
    </div>
  )
}
