import { useState } from 'react'
import { Link } from 'react-router-dom'

import CartaoNoticia from '../components/CartaoNoticia'
import { EsqueletoLista } from '../components/Esqueleto'
import { EstadoErro, EstadoVazio } from '../components/Estado'
import Paginacao from '../components/Paginacao'
import { useAviso } from '../contexts/AvisoContext'
import useListaPaginada from '../hooks/useListaPaginada'
import useSeo from '../hooks/useSeo'
import { social } from '../services/social'
import { tempoRelativo } from '../utils/formatar'

export default function Favoritos() {
  const lista = useListaPaginada((pagina) => social.favoritos({ page: pagina }), [])
  const [removendo, setRemovendo] = useState(null)
  const { mostrar } = useAviso()
  useSeo({ titulo: 'Notícias salvas', caminho: '/meus-favoritos' })

  const remover = async (item) => {
    setRemovendo(item.id)
    try {
      await social.alternarFavorito(item.noticia.id)
      lista.setItens((atuais) => atuais.filter((atual) => atual.id !== item.id))
      mostrar('Removida dos salvos.')
    } catch {
      mostrar('Não foi possível remover agora.', 'erro')
    } finally {
      setRemovendo(null)
    }
  }

  return (
    <div className="container pagina">
      <header className="pagina__cabecalho">
        <div>
          <h1 className="titulo-pagina">Notícias salvas</h1>
          <p className="pagina__descricao">Matérias guardadas para ler com calma.</p>
        </div>
      </header>

      {lista.erro ? <EstadoErro mensagem={lista.erro} aoTentarNovamente={lista.recarregar} /> : null}
      {lista.carregando && !lista.itens.length ? <EsqueletoLista quantidade={3} /> : null}
      {!lista.carregando && !lista.erro && !lista.itens.length ? (
        <EstadoVazio
          icone="marcadorVazio"
          titulo="Nada salvo ainda"
          descricao="Use o botão Salvar em qualquer matéria para guardá-la aqui."
          acao={<Link to="/" className="botao botao--primario">Explorar notícias</Link>}
        />
      ) : null}

      <ul className="lista-itens">
        {lista.itens.map((item) => (
          <li key={item.id} className="lista-itens__item">
            <CartaoNoticia noticia={item.noticia} variante="horizontal" />
            <div className="lista-itens__acoes">
              <span className="cartao__meta">Salva {tempoRelativo(item.criado_em)}</span>
              <button
                type="button"
                className="botao botao--pequeno botao--contorno-perigo"
                onClick={() => remover(item)}
                disabled={removendo === item.id}
              >
                Remover
              </button>
            </div>
          </li>
        ))}
      </ul>
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
