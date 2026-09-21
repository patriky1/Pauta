import axios from 'axios'

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const CHAVE_ACESSO = 'pauta.access'
const CHAVE_REFRESH = 'pauta.refresh'

export const tokens = {
  acesso: () => localStorage.getItem(CHAVE_ACESSO),
  refresh: () => localStorage.getItem(CHAVE_REFRESH),
  salvar(acesso, refresh) {
    if (acesso) localStorage.setItem(CHAVE_ACESSO, acesso)
    if (refresh) localStorage.setItem(CHAVE_REFRESH, refresh)
  },
  limpar() {
    localStorage.removeItem(CHAVE_ACESSO)
    localStorage.removeItem(CHAVE_REFRESH)
  },
}

const api = axios.create({ baseURL: API_URL, timeout: 20000 })

api.interceptors.request.use((config) => {
  const token = tokens.acesso()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let renovando = null

api.interceptors.response.use(
  (resposta) => resposta,
  async (erro) => {
    const original = erro.config || {}
    const status = erro.response?.status

    if (status === 401 && !original._tentouRenovar && tokens.refresh()) {
      original._tentouRenovar = true
      try {
        renovando =
          renovando ||
          axios.post(`${API_URL}/auth/refresh/`, { refresh: tokens.refresh() })
        const { data } = await renovando
        renovando = null
        tokens.salvar(data.access, data.refresh)
        original.headers = { ...original.headers, Authorization: `Bearer ${data.access}` }
        return api(original)
      } catch (falha) {
        renovando = null
        tokens.limpar()
        window.dispatchEvent(new CustomEvent('pauta:sessao-expirada'))
        return Promise.reject(falha)
      }
    }

    erro.mensagem = mensagemDeErro(erro)
    return Promise.reject(erro)
  }
)

export function mensagemDeErro(erro) {
  if (erro.code === 'ECONNABORTED') return 'A conexão demorou demais. Tente de novo.'
  if (!erro.response) return 'Sem conexão com o servidor. Verifique sua internet.'
  const dados = erro.response.data || {}
  if (dados.errors) {
    const primeiro = Object.values(dados.errors)[0]
    if (Array.isArray(primeiro) && primeiro.length) return String(primeiro[0])
    if (typeof primeiro === 'string') return primeiro
  }
  if (dados.detail) return String(dados.detail)
  return 'Não foi possível concluir. Tente novamente.'
}

export default api
