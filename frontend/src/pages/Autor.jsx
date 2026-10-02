import { useState } from 'react'
import { useParams } from 'react-router-dom'

import GradeNoticias from '../components/GradeNoticias'
import Paginacao from '../components/Paginacao'
import { EstadoErro } from '../components/Estado'
import { useAuth } from '../contexts/AuthContext'
import { useAviso } from '../contexts/AvisoContext'
import useListaPaginada from '../hooks/useListaPaginada'
import useRequisicao from '../hooks/useRequisicao'
import useSeo from '../hooks/useSeo'
import { catalogo } from '../services/noticias'
import { social } from '../services/social'
import { iniciais, numero } from '../utils/formatar'

export default function Autor() {
  const { username } = useParams()
  const { autenticado } = useAuth()
  const { mostrar } = useAviso()
  const [seguindo, setSeguindo] = useState(null)

  const { dados: autor, erro, recarregar } = useRequisicao(() => catalogo.autor(username), [username])
  const lista = useListaPaginada((pagina) => catalogo.noticiasDoAutor(username, { page: pagina }), [username])

  useSeo({
    titulo: autor?.nome,
    descricao: autor?.biografia,
    caminho: `/autor/${username}`,
    tipo: 'profile',
    schema: autor
      ? { '@context': 'https://schema.org', '@type': 'Person', name: autor.nome, description: autor.biografia }
      : undefined,
  })

  const estaSeguindo = seguindo === null ? Boolean(autor?.seguindo) : seguindo

  const alternar = async () => {
    if (!autenticado) { mostrar('Entre na sua conta para seguir este autor.', 'erro'); return }
    try {
      const resposta = await social.alternarSeguir('authors', username)
      setSeguindo(resposta.seguindo)
    } catch {
      mostrar('Não foi possível atualizar agora.', 'erro')
    }
  }

  if (erro) return <div className="container"><EstadoErro mensagem={erro} aoTentarNovamente={recarregar} /></div>

  const limpar = (valor = '') => valor.replace('@', '').trim()
  const redes = autor
    ? [
        autor.site && { rotulo: 'Site', url: autor.site },
        autor.twitter && { rotulo: 'X', url: `https://x.com/${limpar(autor.twitter)}` },
        autor.instagram && { rotulo: 'Instagram', url: `https://instagram.com/${limpar(autor.instagram)}` },
        autor.linkedin && {
          rotulo: 'LinkedIn',
          url: autor.linkedin.startsWith('http') ? autor.linkedin : `https://linkedin.com/in/${limpar(autor.linkedin)}`,
        },
      ].filter(Boolean)
    : []

  return (
    <div className="container pagina">
      <header className="perfil-autor bloco">
        {autor?.foto ? (
          <img className="avatar avatar--g" src={autor.foto} alt="" />
        ) : (
          <span className="avatar avatar--g" aria-hidden="true">{iniciais(autor?.nome || '?')}</span>
        )}
        <div className="perfil-autor__info">
          <h1 className="titulo-pagina">{autor?.nome || '…'}</h1>
          {autor?.biografia ? <p className="pagina__descricao">{autor.biografia}</p> : null}
          <div className="cartao__meta" style={{ marginTop: 8, fontSize: 'var(--t-sm)' }}>
            <span>{numero(autor?.total_noticias)} publicações</span>
            <span aria-hidden="true">·</span>
            <span>{numero(autor?.total_visualizacoes)} leituras</span>
          </div>
          {redes.length ? (
            <div className="grupo-botoes" style={{ marginTop: 'var(--e-3)' }}>
              {redes.map((rede) => (
                <a key={rede.rotulo} className="botao botao--pequeno" href={rede.url} target="_blank" rel="noopener noreferrer">
                  {rede.rotulo}
                </a>
              ))}
            </div>
          ) : null}
        </div>
        <button
          type="button"
          className={`botao${estaSeguindo ? '' : ' botao--primario'}`}
          onClick={alternar}
          aria-pressed={estaSeguindo}
        >
          {estaSeguindo ? 'Seguindo' : 'Seguir'}
        </button>
      </header>

      <section className="secao" style={{ borderTop: 0 }}>
        <div className="secao__cabecalho"><h2 className="secao__titulo">Últimas publicações</h2></div>
        <GradeNoticias
          noticias={lista.itens}
          carregando={lista.carregando}
          erro={lista.erro}
          aoRecarregar={lista.recarregar}
        />
        <Paginacao
          pagina={lista.pagina}
          temMais={lista.temMais}
          carregando={lista.carregando}
          total={lista.total}
          aoCarregarMais={lista.carregarMais}
        />
      </section>
    </div>
  )
}
