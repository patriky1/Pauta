import api from './api'

const lista = (url, params) => api.get(url, { params }).then((r) => r.data)

// categorias mudam raramente e são usadas no cabeçalho, rodapé e filtros:
// uma única requisição a cada 5 minutos atende a página inteira.
let cacheCategorias = null
let cacheCategoriasEm = 0
function categoriasEmCache(params) {
  if (params && Object.keys(params).length) return lista('/categories/', params)
  const agora = Date.now()
  if (!cacheCategorias || agora - cacheCategoriasEm > 5 * 60 * 1000) {
    cacheCategoriasEm = agora
    cacheCategorias = lista('/categories/').catch((erro) => {
      cacheCategorias = null
      throw erro
    })
  }
  return cacheCategorias
}

export const noticias = {
  listar: (params) => lista('/news/', params),
  ultimas: (params) => lista('/news/latest/', params),
  maisLidas: (periodo = 'semana', params = {}) =>
    lista('/news/most-read/', { periodo, ...params }),
  paraVoce: (params) => lista('/news/for-you/', params),
  seguindo: (params) => lista('/news/seguindo/', params),
  destaques: () => lista('/news/destaques/'),
  urgentes: () => lista('/news/breaking/'),
  tendencias: () => lista('/news/trending/'),
  
  // 🟢 CORREÇÃO: encodeURIComponent previne erros em slugs com acentos ou caracteres especiais
  detalhe: (slug) => lista(`/news/${encodeURIComponent(slug)}/`),
  compartilhar: (slug, rede) => api.post(`/news/${encodeURIComponent(slug)}/compartilhar/`, { rede }),
  tempoLeitura: (slug, segundos) => api.post(`/news/${encodeURIComponent(slug)}/tempo-leitura/`, { segundos }),
}

export const catalogo = {
  categorias: (params) => categoriasEmCache(params),
  categoria: (slug) => lista(`/categories/${encodeURIComponent(slug)}/`),
  tags: (params) => lista('/tags/', params),
  autores: (params) => lista('/authors/', params),
  autor: (username) => lista(`/authors/${encodeURIComponent(username)}/`),
  noticiasDoAutor: (username, params) => lista(`/authors/${encodeURIComponent(username)}/noticias/`, params),
  buscar: (params) => lista('/search/', params),
  videos: (params) => lista('/videos/', params),
  video: (slug) => lista(`/videos/${encodeURIComponent(slug)}/`),
  coberturas: (params) => lista('/live/', params),
  cobertura: (slug) => lista(`/live/${encodeURIComponent(slug)}/`),
  anuncios: (posicao) => lista('/ads/', { posicao }),
  tendencias: () => lista('/analytics/trending/'),
  registrarEvento: (payload) => api.post('/analytics/', payload).catch(() => null),
}