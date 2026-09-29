import api, { tokens } from './api'

export const authService = {
  async entrar(login, senha) {
    const { data } = await api.post('/auth/login/', { username: login, password: senha })
    tokens.salvar(data.access, data.refresh)
    return data.user
  },
  async cadastrar(dados) {
    const { data } = await api.post('/auth/register/', dados)
    tokens.salvar(data.access, data.refresh)
    return data.user
  },
  async sair() {
    try {
      await api.post('/auth/logout/')
    } finally {
      tokens.limpar()
    }
  },
  async eu() {
    const { data } = await api.get('/auth/me/')
    return data
  },
  async atualizarPerfil(dados) {
    const temArquivo = dados instanceof FormData
    const { data } = await api.patch('/auth/me/', dados, {
      headers: temArquivo ? { 'Content-Type': 'multipart/form-data' } : undefined,
    })
    return data
  },
  alterarSenha: (senha_atual, nova_senha) =>
    api.post('/auth/password/change/', { senha_atual, nova_senha }).then((r) => r.data),
  pedirReset: (email) => api.post('/auth/password/reset/', { email }).then((r) => r.data),
  confirmarReset: (payload) =>
    api.post('/auth/password/reset/confirm/', payload).then((r) => r.data),
}

export default authService
