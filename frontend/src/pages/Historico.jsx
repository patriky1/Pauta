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

export default function Historico() {
  const lista = useListaPaginada((pagina) => social.historico({ page: pagina }), [])
  const { mostrar } = useAviso()
  useSeo({ titulo: 'Histórico de leitura', caminho: '/historico' })

  const limpar = async () => {
    if (!window.confirm('Apagar todo o seu histórico de leitura?')) return
    try {
      await social.limparHistorico()
      lista.setItens([])
      mostrar('Histórico apagado.')
    } catch {
      mostrar('Não foi possível apagar agora.', 'erro')
    }
  }

  return (
    <div className="container pagina">
      <header className="pagina__cabecalho">
        <div>
          <h1 className="titulo-pagina">Histórico</h1>
          <p className="pagina__descricao">As matérias que você abriu, da mais recente para a mais antiga.</p>
        </div>
        {lista.itens.length ? (
          <button type="button" className="botao botao--contorno-perigo" onClick={limpar}>Limpar histórico</button>
        ) : null}
      </header>

      {lista.erro ? <EstadoErro mensagem={lista.erro} aoTentarNovamente={lista.recarregar} /> : null}
      {lista.carregando && !lista.itens.length ? <EsqueletoLista quantidade={3} /> : null}
      {!lista.carregando && !lista.erro && !lista.itens.length ? (
        <EstadoVazio
          icone="relogio"
          titulo="Seu histórico está vazio"
          descricao="As matérias que você abrir aparecem aqui."
          acao={<Link to="/" className="botao botao--primario">Começar a ler</Link>}
        />
      ) : null}

      <ul className="lista-itens">
        {lista.itens.map((item) => (
          <li key={item.id} className="lista-itens__item">
            <CartaoNoticia noticia={item.noticia} variante="horizontal" />
            <div className="lista-itens__acoes">
              <span className="cartao__meta">Lida {tempoRelativo(item.visto_em)}</span>
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
