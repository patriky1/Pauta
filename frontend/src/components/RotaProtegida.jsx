import { Navigate, useLocation } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext'
import { EsqueletoLista } from './Esqueleto'

export default function RotaProtegida({ children, exigeRedacao = false }) {
  const { autenticado, ehRedacao, carregando } = useAuth()
  const local = useLocation()

  if (carregando) return <div className="container" style={{ padding: 32 }}><EsqueletoLista quantidade={3} /></div>
  if (!autenticado) return <Navigate to="/entrar" state={{ de: local.pathname }} replace />
  if (exigeRedacao && !ehRedacao) return <Navigate to="/" replace />
  return children
}
