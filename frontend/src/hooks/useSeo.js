import { useEffect } from 'react'

import { NOME_SITE, URL_SITE } from '../utils/constantes'

function definirMeta(seletor, atributo, valor, conteudo) {
  let tag = document.head.querySelector(seletor)
  if (!conteudo) {
    tag?.remove()
    return
  }
  if (!tag) {
    tag = document.createElement('meta')
    tag.setAttribute(atributo, valor)
    document.head.appendChild(tag)
  }
  tag.setAttribute('content', conteudo)
}

function definirLink(rel, href) {
  if (!href) return
  let tag = document.head.querySelector(`link[rel="${rel}"]`)
  if (!tag) {
    tag = document.createElement('link')
    tag.setAttribute('rel', rel)
    document.head.appendChild(tag)
  }
  tag.setAttribute('href', href)
}

/** Title, description, canonical, Open Graph, Twitter Cards e Schema.org. */
export default function useSeo({ titulo, descricao, imagem, caminho, tipo = 'website', schema } = {}) {
  // serializa o schema para não reexecutar o efeito a cada renderização
  const schemaJson = schema ? JSON.stringify(schema) : ''

  useEffect(() => {
    const tituloFinal = titulo ? `${titulo} — ${NOME_SITE}` : `${NOME_SITE} — notícias em tempo real`
    const url = `${URL_SITE}${caminho || window.location.pathname}`
    document.title = tituloFinal

    definirMeta('meta[name="description"]', 'name', 'description', descricao)
    definirLink('canonical', url)

    definirMeta('meta[property="og:title"]', 'property', 'og:title', tituloFinal)
    definirMeta('meta[property="og:description"]', 'property', 'og:description', descricao)
    definirMeta('meta[property="og:type"]', 'property', 'og:type', tipo)
    definirMeta('meta[property="og:url"]', 'property', 'og:url', url)
    definirMeta('meta[property="og:image"]', 'property', 'og:image', imagem)
    definirMeta('meta[property="og:site_name"]', 'property', 'og:site_name', NOME_SITE)

    definirMeta('meta[name="twitter:card"]', 'name', 'twitter:card', imagem ? 'summary_large_image' : 'summary')
    definirMeta('meta[name="twitter:title"]', 'name', 'twitter:title', tituloFinal)
    definirMeta('meta[name="twitter:description"]', 'name', 'twitter:description', descricao)
    definirMeta('meta[name="twitter:image"]', 'name', 'twitter:image', imagem)

    const id = 'dados-estruturados'
    document.getElementById(id)?.remove()
    if (schemaJson) {
      const script = document.createElement('script')
      script.type = 'application/ld+json'
      script.id = id
      script.textContent = schemaJson
      document.head.appendChild(script)
    }
  }, [titulo, descricao, imagem, caminho, tipo, schemaJson])
}
