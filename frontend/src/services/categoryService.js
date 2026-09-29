import api from './api'

export const categoryService = {
  listar: (params) => api.get('/categories/', { params }).then((r) => r.data),
  detalhe: (slug) => api.get(`/categories/${slug}/`).then((r) => r.data),
  criar: (dados) => api.post('/categories/', dados).then((r) => r.data),
  atualizar: (slug, dados) => api.patch(`/categories/${slug}/`, dados).then((r) => r.data),
  excluir: (slug) => api.delete(`/categories/${slug}/`),
  tags: (params) => api.get('/tags/', { params }).then((r) => r.data),
  criarTag: (nome) => api.post('/tags/', { nome }).then((r) => r.data),
  excluirTag: (slug) => api.delete(`/tags/${slug}/`),
}

export const authorService = {
  listar: (params) => api.get('/authors/', { params }).then((r) => r.data),
  detalhe: (username) => api.get(`/authors/${username}/`).then((r) => r.data),
  noticias: (username, params) =>
    api.get(`/authors/${username}/noticias/`, { params }).then((r) => r.data),
}

export default categoryService
