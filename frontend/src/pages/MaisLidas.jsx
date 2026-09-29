import { useCallback, useState } from 'react'

import AbasFeed from '../components/AbasFeed'
import GradeNoticias from '../components/GradeNoticias'
import Paginacao from '../components/Paginacao'
import useListaPaginada from '../hooks/useListaPaginada'
import useSeo from '../hooks/useSeo'
import { noticias as servico } from '../services/noticias'

const PERIODOS = [
  { chave: 'hoje', rotulo: 'Hoje' },
  { chave: 'semana', rotulo: 'Na semana' },
  { chave: 'mes', rotulo: 'No mês' },
]

export default function MaisLidas() {
  const [periodo, setPeriodo] = useState('hoje')
  useSeo({ titulo: 'Mais lidas', caminho: '/mais-lidas' })

  const buscar = useCallback((pagina) => servico.maisLidas(periodo, { page: pagina }), [periodo])
  const lista = useListaPaginada(buscar, [periodo])

  return (
    <div className="container pagina">
      <header className="pagina__cabecalho">
        <div>
          <h1 className="titulo-pagina">Mais lidas</h1>
          <p className="pagina__descricao">O que os leitores do Pauta mais abriram no período.</p>
        </div>
      </header>
      <AbasFeed abas={PERIODOS} ativa={periodo} aoTrocar={setPeriodo} />
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
    </div>
  )
}
