import CartaoNoticia from './CartaoNoticia'
import { EsqueletoLista } from './Esqueleto'
import { EstadoErro, EstadoVazio } from './Estado'

export default function GradeNoticias({
  noticias = [],
  carregando,
  erro,
  aoRecarregar,
  vazioTitulo = 'Sem notícias por aqui',
  vazioDescricao = 'Assim que algo novo for publicado, aparece nesta lista.',
  vazioAcao,
  colunas,
}) {
  if (erro && noticias.length === 0) return <EstadoErro mensagem={erro} aoTentarNovamente={aoRecarregar} />
  if (carregando && noticias.length === 0) return <EsqueletoLista />
  if (!carregando && noticias.length === 0) {
    return <EstadoVazio titulo={vazioTitulo} descricao={vazioDescricao} acao={vazioAcao} />
  }

  return (
    <div className={`grade${colunas === 2 ? ' grade--2' : ''}`}>
      {noticias.map((noticia, indice) => (
        <CartaoNoticia key={noticia.id} noticia={noticia} prioridade={indice < 2} />
      ))}
    </div>
  )
}
