import { useEffect } from 'react'
import { BrowserRouter, useLocation } from 'react-router-dom'

import { AuthProvider } from './contexts/AuthContext'
import { AvisoProvider } from './contexts/AvisoContext'
import { TemaProvider } from './contexts/TemaContext'
import Rotas from './routes/Rotas'

function RolarAoTrocarDeRota() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'instant' }) }, [pathname])
  return null
}

export default function App() {
  return (
    <BrowserRouter>
      <TemaProvider>
        <AvisoProvider>
          <AuthProvider>
            <RolarAoTrocarDeRota />
            <Rotas />
          </AuthProvider>
        </AvisoProvider>
      </TemaProvider>
    </BrowserRouter>
  )
}
