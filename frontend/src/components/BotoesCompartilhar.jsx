import { useAviso } from '../contexts/AvisoContext'
import { noticias } from '../services/noticias'
import { URL_SITE } from '../utils/constantes'
import Icone from './Icone'

export default function BotoesCompartilhar({ noticia }) {
  const { mostrar } = useAviso()
  const url = `${URL_SITE}/noticia/${noticia.slug}`

  const registrar = (rede) => noticias.compartilhar(noticia.slug, rede).catch(() => null)

  const abrir = (rede, destino) => {
    registrar(rede)
    window.open(destino, '_blank', 'noopener,noreferrer,width=600,height=520')
  }

  const copiar = async () => {
    try {
      await navigator.clipboard.writeText(url)
      registrar('link')
      mostrar('Link copiado.')
    } catch {
      mostrar('Não foi possível copiar o link.', 'erro')
    }
  }

  const compartilharNativo = async () => {
    if (!navigator.share) return copiar()
    try {
      await navigator.share({ title: noticia.titulo, text: noticia.resumo, url })
      registrar('nativo')
    } catch {
      /* usuário cancelou */
    }
    return null
  }

  return (
    <div className="materia__barra" role="group" aria-label="Compartilhar">
      <button type="button" className="botao" onClick={compartilharNativo}>
        <Icone nome="compartilhar" tamanho={16} /> Compartilhar
      </button>
      <button
        type="button"
        className="botao"
        onClick={() => abrir('whatsapp', `https://wa.me/?text=${encodeURIComponent(`${noticia.titulo} ${url}`)}`)}
      >
        WhatsApp
      </button>
      <button
        type="button"
        className="botao"
        onClick={() => abrir('x', `https://twitter.com/intent/tweet?text=${encodeURIComponent(noticia.titulo)}&url=${encodeURIComponent(url)}`)}
      >
        X
      </button>
      <button
        type="button"
        className="botao"
        onClick={() => abrir('facebook', `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`)}
      >
        Facebook
      </button>
      <button type="button" className="botao" onClick={copiar}>Copiar link</button>
    </div>
  )
}
