import api from './api'

export const interactionService = {
  favoritos: (params) => api.get('/favorites/', { params }).then((r) => r.data),
  alternarFavorito: (slug) => api.post('/favorites/', { noticia: slug }).then((r) => r.data),
  historico: (params) => api.get('/history/', { params }).then((r) => r.data),
  limparHistorico: () => api.delete('/history/limpar/'),
  seguidos: (recurso) => api.get(`/follow/${recurso}/`).then((r) => r.data),
  alternarSeguir: (recurso, payload) =>
    api.post(`/follow/${recurso}/`, payload).then((r) => r.data),
  interesses: () => api.get('/interests/').then((r) => r.data),
}

export default interactionService
