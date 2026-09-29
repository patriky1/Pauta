import api from './api'

export const social = {
  comentarios: (noticiaId, params) =>
    api.get('/comments/', { params: { noticia: noticiaId, ...params } }).then((r) => r.data),
  comentar: (payload) => api.post('/comments/', payload).then((r) => r.data),
  editarComentario: (id, conteudo) =>
    api.patch(`/comments/${id}/`, { conteudo }).then((r) => r.data),
  excluirComentario: (id) => api.delete(`/comments/${id}/`),
  curtirComentario: (id) => api.post(`/comments/${id}/curtir/`).then((r) => r.data),
  denunciar: (payload) => api.post('/reports/', payload).then((r) => r.data),

  favoritos: (params) => api.get('/favorites/', { params }).then((r) => r.data),
  alternarFavorito: (noticiaId) =>
    api.post('/favorites/', { noticia: noticiaId }).then((r) => r.data),

  historico: (params) => api.get('/history/', { params }).then((r) => r.data),
  limparHistorico: () => api.delete('/history/limpar/'),

  seguidos: (tipo) => api.get(`/follow/${tipo}/`).then((r) => r.data),
  alternarSeguir: (tipo, valor) =>
    api.post(`/follow/${tipo}/`, { valor }).then((r) => r.data),

  notificacoes: (params) => api.get('/notifications/', { params }).then((r) => r.data),
  contadorNotificacoes: () => api.get('/notifications/contador/').then((r) => r.data),
  marcarLida: (id) => api.post(`/notifications/${id}/lida/`),
  marcarTodasLidas: () => api.post('/notifications/ler-todas/'),
}
