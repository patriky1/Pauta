import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { Esqueleto } from '../components/Esqueleto'
import { EstadoErro } from '../components/Estado'
import { useAviso } from '../contexts/AvisoContext'
import useRequisicao from '../hooks/useRequisicao'
import useSeo from '../hooks/useSeo'
import { catalogo } from '../services/noticias'
import { social } from '../services/social'

export default function Interesses() {
  const { mostrar } = useAviso()
  const [seguidas, setSeguidas] = useState([])
  const [processando, setProcessando] = useState(null)
  const { dados, carregando, erro, recarregar } = useRequisicao(() => catalogo.categorias(), [])
  useSeo({ titulo: 'Seus interesses', caminho: '/interesses' })

  const categorias = Array.isArray(dados) ? dados : dados?.results || []

  useEffect(() => {
    social
      .seguidos('categories')
      .then((lista) => setSeguidas((lista || []).map((item) => item.slug)))
      .catch(() => setSeguidas([]))
  }, [])

  const alternar = async (categoria) => {
    setProcessando(categoria.slug)
    try {
      const resposta = await social.alternarSeguir('categories', categoria.slug)
      setSeguidas((atuais) =>
        resposta.seguindo ? [...atuais, categoria.slug] : atuais.filter((slug) => slug !== categoria.slug)
      )
    } catch {
      mostrar('Não foi possível atualizar agora.', 'erro')
    } finally {
      setProcessando(null)
    }
  }

  if (erro) return <div className="container"><EstadoErro mensagem={erro} aoTentarNovamente={recarregar} /></div>

  return (
    <div className="container pagina">
      <header className="pagina__cabecalho">
        <div>
          <h1 className="titulo-pagina">Seus interesses</h1>
          <p className="pagina__descricao">
            Escolha as editorias que devem pesar mais no seu feed “Para você”. Você pode mudar quando quiser.
          </p>
        </div>
        <Link to="/" className="botao botao--primario">Ver meu feed</Link>
      </header>

      <div className="bloco">
        <p className="cartao__meta" style={{ marginBottom: 'var(--e-3)', fontSize: 'var(--t-sm)' }}>
          {seguidas.length
            ? `${seguidas.length} ${seguidas.length === 1 ? 'editoria selecionada' : 'editorias selecionadas'}`
            : 'Nenhuma editoria selecionada ainda'}
        </p>
        {carregando ? (
          <Esqueleto altura={80} />
        ) : (
          <div className="grupo-botoes">
            {categorias.map((categoria) => {
              const ativa = seguidas.includes(categoria.slug)
              return (
                <button
                  key={categoria.id}
                  type="button"
                  className="botao"
                  onClick={() => alternar(categoria)}
                  aria-pressed={ativa}
                  disabled={processando === categoria.slug}
                >
                  {ativa ? '✓ ' : '+ '}
                  {categoria.nome}
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
