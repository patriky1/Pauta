import api from './api'

export const newsService = {
  listar: (params) => api.get('/news/', { params }).then((r) => r.data),
  detalhe: (slug) => api.get(`/news/${slug}/`).then((r) => r.data),
  destaques: () => api.get('/news/destaques/').then((r) => r.data),
  urgentes: () => api.get('/news/breaking/').then((r) => r.data),
  ultimas: (params) => api.get('/news/latest/', { params }).then((r) => r.data),
  maisLidas: (params) => api.get('/news/most-read/', { params }).then((r) => r.data),
  paraVoce: (params) => api.get('/news/for-you/', { params }).then((r) => r.data),
  seguindo: (params) => api.get('/news/seguindo/', { params }).then((r) => r.data),
  tendencias: () => api.get('/news/trending/').then((r) => r.data),
  compartilhar: (slug, rede) => api.post(`/news/${slug}/compartilhar/`, { rede }),
  registrarTempo: (slug, segundos) => api.post(`/news/${slug}/tempo-leitura/`, { segundos }),
  buscar: (params) => api.get('/search/', { params }).then((r) => r.data),

  // área editorial
  listarRedacao: (params) => api.get('/admin/news/', { params }).then((r) => r.data),
  obterRedacao: (slug) => api.get(`/admin/news/${slug}/`).then((r) => r.data),
  criar: (dados) => api.post('/admin/news/', dados).then((r) => r.data),
  atualizar: (slug, dados) => api.patch(`/admin/news/${slug}/`, dados).then((r) => r.data),
  excluir: (slug) => api.delete(`/admin/news/${slug}/`),
  publicar: (slug) => api.post(`/admin/news/${slug}/publicar/`).then((r) => r.data),
  arquivar: (slug) => api.post(`/admin/news/${slug}/arquivar/`).then((r) => r.data),
  enviarRevisao: (slug) => api.post(`/admin/news/${slug}/revisao/`).then((r) => r.data),
  alternarDestaque: (slug) => api.post(`/admin/news/${slug}/destacar/`).then((r) => r.data),
  alternarUrgente: (slug) => api.post(`/admin/news/${slug}/urgente/`).then((r) => r.data),
}

export default newsService
