import api from './api'

export const painel = {
  resumo: () => api.get('/analytics/dashboard/').then((r) => r.data),

  noticias: (params) => api.get('/admin/news/', { params }).then((r) => r.data),
  noticia: (slug) => api.get(`/admin/news/${slug}/`).then((r) => r.data),
  criarNoticia: (payload) => api.post('/admin/news/', payload).then((r) => r.data),
  atualizarNoticia: (slug, payload) =>
    api.patch(`/admin/news/${slug}/`, payload).then((r) => r.data),
  excluirNoticia: (slug) => api.delete(`/admin/news/${slug}/`),
  publicar: (slug) => api.post(`/admin/news/${slug}/publicar/`).then((r) => r.data),
  arquivar: (slug) => api.post(`/admin/news/${slug}/arquivar/`).then((r) => r.data),
  enviarRevisao: (slug) => api.post(`/admin/news/${slug}/revisao/`).then((r) => r.data),
  destacar: (slug) => api.post(`/admin/news/${slug}/destacar/`).then((r) => r.data),
  marcarUrgente: (slug) => api.post(`/admin/news/${slug}/urgente/`).then((r) => r.data),

  usuarios: (params) => api.get('/admin/users/', { params }).then((r) => r.data),
  bloquear: (id, motivo) =>
    api.post(`/admin/users/${id}/bloquear/`, { motivo }).then((r) => r.data),
  desbloquear: (id) => api.post(`/admin/users/${id}/desbloquear/`).then((r) => r.data),
  alterarFuncao: (id, tipo_usuario) =>
    api.post(`/admin/users/${id}/funcao/`, { tipo_usuario }).then((r) => r.data),

  comentariosPendentes: (params) =>
    api.get('/comments/', { params: { ...params, todos: 1 } }).then((r) => r.data),
  aprovarComentario: (id) => api.post(`/comments/${id}/aprovar/`),
  ocultarComentario: (id) => api.post(`/comments/${id}/ocultar/`),
  denuncias: (params) => api.get('/reports/', { params }).then((r) => r.data),

  criarCategoria: (payload) => api.post('/categories/', payload).then((r) => r.data),
  coberturas: (params) => api.get('/live/', { params }).then((r) => r.data),
  criarCobertura: (payload) => api.post('/live/', payload).then((r) => r.data),
  adicionarAtualizacao: (slug, payload) =>
    api.post(`/live/${slug}/atualizacoes/`, payload).then((r) => r.data),
  encerrarCobertura: (slug) => api.post(`/live/${slug}/encerrar/`).then((r) => r.data),
}
