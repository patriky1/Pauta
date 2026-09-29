import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import LinhaAoVivo from '../components/LinhaAoVivo'
import { Esqueleto } from '../components/Esqueleto'
import { EstadoErro, EstadoVazio } from '../components/Estado'
import useIntervalo from '../hooks/useIntervalo'
import useRequisicao from '../hooks/useRequisicao'
import useSeo from '../hooks/useSeo'
import { catalogo } from '../services/noticias'
import { hora, tempoRelativo } from '../utils/formatar'

function EsqueletoAoVivo() {
  return (
    <div className="materia">
      <Esqueleto altura={14} largura="18%" />
      <div style={{ height: 14 }} />
      <Esqueleto altura={34} largura="80%" />
      <div style={{ height: 24 }} />
      {[0, 1, 2].map((i) => (
        <div key={i} style={{ marginBottom: 18 }}>
          <Esqueleto altura={12} largura="12%" />
          <div style={{ height: 8 }} />
          <Esqueleto altura={48} />
        </div>
      ))}
    </div>
  )
}

export default function AoVivo() {
  const { slug } = useParams()
  const [atualizadoEm, setAtualizadoEm] = useState(null)

  const buscar = useCallback(() => (slug ? catalogo.cobertura(slug) : catalogo.coberturas()), [slug])
  const { dados, carregando, erro, recarregar } = useRequisicao(buscar, [slug])

  useEffect(() => { if (dados) setAtualizadoEm(new Date()) }, [dados])

  const noAr = slug && dados?.status === 'AO_VIVO'
  // cobertura no ar se atualiza sozinha a cada 30s, sem piscar a tela
  useIntervalo(() => { if (!document.hidden) recarregar({ silencioso: true }) }, noAr ? 30000 : 0)

  useSeo({
    titulo: slug ? dados?.titulo : 'Ao vivo',
    descricao: slug ? dados?.resumo : 'Coberturas ao vivo em andamento.',
    caminho: slug ? `/ao-vivo/${slug}` : '/ao-vivo',
  })

  if (erro) return <div className="container"><EstadoErro mensagem={erro} aoTentarNovamente={recarregar} /></div>

  // --- lista de coberturas
  if (!slug) {
    const coberturas = Array.isArray(dados?.results) ? dados.results : []
    return (
      <div className="container pagina">
        <header className="pagina__cabecalho">
          <div>
            <h1 className="titulo-pagina">Ao vivo</h1>
            <p className="pagina__descricao">Acontecimentos acompanhados minuto a minuto pela redação.</p>
          </div>
        </header>

        {carregando ? <Esqueleto altura={160} /> : null}
        {!carregando && !coberturas.length ? (
          <EstadoVazio
            icone="raio"
            titulo="Nenhuma cobertura no ar"
            descricao="Quando um acontecimento pedir cobertura minuto a minuto, ela aparece aqui."
          />
        ) : null}

        <div className="grade grade--2 grade--manter">
          {coberturas.map((cobertura) => (
            <article key={cobertura.id} className="bloco">
              <Link to={`/ao-vivo/${cobertura.slug}`} className="cartao__link" style={{ gap: 8 }}>
                <div className="cartao__selos">
                  <span className={`selo${cobertura.status === 'AO_VIVO' ? ' selo--exclusivo' : ' selo--linha'}`}>
                    {cobertura.status === 'AO_VIVO' ? '● No ar' : 'Encerrada'}
                  </span>
                  {cobertura.categoria ? <span className="selo">{cobertura.categoria.nome}</span> : null}
                </div>
                <h2 className="cartao__titulo" style={{ fontSize: 'var(--t-xl)' }}>{cobertura.titulo}</h2>
                {cobertura.resumo ? <p className="cartao__resumo">{cobertura.resumo}</p> : null}
                {cobertura.ultima_atualizacao ? (
                  <p className="cartao__meta" style={{ margin: 0 }}>
                    Última atualização {tempoRelativo(cobertura.ultima_atualizacao.horario)}
                  </p>
                ) : null}
              </Link>
            </article>
          ))}
        </div>
      </div>
    )
  }

  // --- cobertura específica (confere se os dados já são desta cobertura)
  if (carregando || !dados || dados.slug !== slug) {
    return <div className="container"><EsqueletoAoVivo /></div>
  }

  return (
    <div className="container">
      <article className="materia">
        <div className="cartao__selos">
          <span className={`selo${noAr ? ' selo--exclusivo' : ' selo--linha'}`}>
            {noAr ? '● Ao vivo agora' : 'Cobertura encerrada'}
          </span>
          {dados.categoria ? <span className="selo">{dados.categoria.nome}</span> : null}
        </div>
        <h1 className="materia__titulo">{dados.titulo}</h1>
        {dados.resumo ? <p className="materia__linha-fina">{dados.resumo}</p> : null}
        <div className="materia__assinatura">
          <span className="cartao__meta" style={{ fontSize: 'var(--t-sm)' }}>
            Por {dados.criado_por?.nome || 'Redação'} · começou {tempoRelativo(dados.iniciada_em)}
          </span>
          {noAr && atualizadoEm ? (
            <span className="ao-vivo__atualizado">
              <span className="ao-vivo-ponto" aria-hidden="true" />
              Atualiza sozinha · {hora(atualizadoEm)}
            </span>
          ) : null}
        </div>
        <div style={{ marginTop: 'var(--e-5)' }}>
          <LinhaAoVivo atualizacoes={dados.atualizacoes || []} />
        </div>
      </article>
    </div>
  )
}
