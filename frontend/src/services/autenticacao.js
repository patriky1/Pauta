import api, { tokens } from './api'

export const autenticacao = {
  async entrar(usuario, senha) {
    const { data } = await api.post('/auth/login/', { username: usuario, password: senha })
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
  async perfil() {
    const { data } = await api.get('/auth/me/')
    return data
  },
  async atualizarPerfil(dados) {
    const { data } = await api.patch('/auth/me/', dados)
    return data
  },
  alterarSenha: (senha_atual, nova_senha) =>
    api.post('/auth/password/change/', { senha_atual, nova_senha }),
  pedirReset: (email) => api.post('/auth/password/reset/', { email }),
  confirmarReset: (uid, token, nova_senha) =>
    api.post('/auth/password/reset/confirm/', { uid, token, nova_senha }),
}
