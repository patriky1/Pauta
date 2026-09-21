import { useState } from 'react'

import CartaoVideo from '../components/CartaoVideo'
import Modal from '../components/Modal'
import { EsqueletoLista } from '../components/Esqueleto'
import { EstadoErro, EstadoVazio } from '../components/Estado'
import useRequisicao from '../hooks/useRequisicao'
import useSeo from '../hooks/useSeo'
import { catalogo } from '../services/noticias'

function incorporar(video) {
  if (!video) return null
  if (video.plataforma === 'YOUTUBE' && video.id_externo) {
    return `https://www.youtube-nocookie.com/embed/${video.id_externo}?autoplay=1&rel=0`
  }
  if (video.plataforma === 'VIMEO' && video.id_externo) {
    return `https://player.vimeo.com/video/${video.id_externo}?autoplay=1`
  }
  return null
}

export default function Videos() {
  const [aberto, setAberto] = useState(null)
  const { dados, carregando, erro, recarregar } = useRequisicao(() => catalogo.videos(), [])
  useSeo({ titulo: 'Vídeos', descricao: 'Reportagens em vídeo do Pauta.', caminho: '/videos' })

  const videos = Array.isArray(dados) ? dados : dados?.results || []
  const url = incorporar(aberto)

  return (
    <div className="container pagina">
      <header className="pagina__cabecalho">
        <div>
          <h1 className="titulo-pagina">Vídeos</h1>
          <p className="pagina__descricao">As principais pautas explicadas em poucos minutos.</p>
        </div>
      </header>

      {erro ? <EstadoErro mensagem={erro} aoTentarNovamente={recarregar} /> : null}
      {carregando ? <EsqueletoLista /> : null}
      {!carregando && !erro && !videos.length ? (
        <EstadoVazio icone="video" titulo="Nenhum vídeo publicado" descricao="A redação publica novos vídeos toda semana." />
      ) : null}

      {!carregando && videos.length ? (
        <div className="grade grade--manter">
          {videos.map((video) => (
            <CartaoVideo key={video.id} video={video} aoAbrir={setAberto} />
          ))}
        </div>
      ) : null}

      <Modal aberto={Boolean(aberto)} titulo={aberto?.titulo} aoFechar={() => setAberto(null)} largo>
        <div style={{ aspectRatio: '16 / 9', background: '#000', borderRadius: 10, overflow: 'hidden' }}>
          {url ? (
            <iframe
              src={url}
              title={aberto?.titulo}
              style={{ width: '100%', height: '100%', border: 0 }}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; picture-in-picture"
              allowFullScreen
            />
          ) : aberto?.url ? (
            <video controls autoPlay src={aberto.url} style={{ width: '100%', height: '100%' }} />
          ) : null}
        </div>
        {aberto?.descricao ? <p style={{ marginTop: 12, color: 'var(--grafite)' }}>{aberto.descricao}</p> : null}
      </Modal>
    </div>
  )
}
