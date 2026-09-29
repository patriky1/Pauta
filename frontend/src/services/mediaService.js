import api from './api'

export const videoService = {
  listar: (params) => api.get('/videos/', { params }).then((r) => r.data),
  detalhe: (slug) => api.get(`/videos/${slug}/`).then((r) => r.data),
  criar: (dados) => api.post('/videos/', dados).then((r) => r.data),
}

export const liveService = {
  listar: (params) => api.get('/live/', { params }).then((r) => r.data),
  detalhe: (slug) => api.get(`/live/${slug}/`).then((r) => r.data),
  criar: (dados) => api.post('/live/', dados).then((r) => r.data),
  adicionarAtualizacao: (slug, dados) =>
    api.post(`/live/${slug}/atualizacoes/`, dados).then((r) => r.data),
  encerrar: (slug) => api.post(`/live/${slug}/encerrar/`).then((r) => r.data),
}

export const adService = {
  listar: (posicao) => api.get('/ads/', { params: { posicao } }).then((r) => r.data),
  registrarClique: (id) => api.post(`/ads/${id}/clique/`),
}

export const analyticsService = {
  painel: () => api.get('/analytics/').then((r) => r.data),
  registrarEvento: (payload) => api.post('/analytics/eventos/', payload).catch(() => null),
  tendencias: (horas) => api.get('/trending/', { params: { horas } }).then((r) => r.data),
}

export const adminUserService = {
  listar: (params) => api.get('/admin/users/', { params }).then((r) => r.data),
  bloquear: (id, motivo) => api.post(`/admin/users/${id}/bloquear/`, { motivo }).then((r) => r.data),
  desbloquear: (id) => api.post(`/admin/users/${id}/desbloquear/`).then((r) => r.data),
  alterarFuncao: (id, tipo_usuario) =>
    api.post(`/admin/users/${id}/funcao/`, { tipo_usuario }).then((r) => r.data),
}
