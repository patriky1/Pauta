import api from './api'

export const notificationService = {
  listar: (params) => api.get('/notifications/', { params }).then((r) => r.data),
  contador: () => api.get('/notifications/contador/').then((r) => r.data),
  marcarLida: (id) => api.post(`/notifications/${id}/lida/`).then((r) => r.data),
  lerTodas: () => api.post('/notifications/ler-todas/').then((r) => r.data),
  excluir: (id) => api.delete(`/notifications/${id}/`),
}

export default notificationService
