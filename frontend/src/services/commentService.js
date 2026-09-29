import api from './api'

export const commentService = {
  listar: (slugNoticia, params) =>
    api.get('/comments/', { params: { noticia: slugNoticia, ...params } }).then((r) => r.data),
  criar: (dados) => api.post('/comments/', dados).then((r) => r.data),
  editar: (id, conteudo) => api.patch(`/comments/${id}/`, { conteudo }).then((r) => r.data),
  excluir: (id) => api.delete(`/comments/${id}/`),
  curtir: (id) => api.post(`/comments/${id}/curtir/`).then((r) => r.data),
  denunciar: (id, motivo, descricao) =>
    api.post(`/comments/${id}/denunciar/`, { motivo, descricao }).then((r) => r.data),

  // moderação
  fila: (params) => api.get('/admin/moderation/', { params }).then((r) => r.data),
  aprovar: (id) => api.post(`/admin/moderation/${id}/aprovar/`).then((r) => r.data),
  ocultar: (id) => api.post(`/admin/moderation/${id}/ocultar/`).then((r) => r.data),
  remover: (id) => api.post(`/admin/moderation/${id}/remover/`).then((r) => r.data),
  denuncias: (params) => api.get('/admin/reports/', { params }).then((r) => r.data),
  resolverDenuncia: (id) => api.post(`/admin/reports/${id}/resolver/`).then((r) => r.data),
}

export default commentService
