import { Suspense, lazy } from 'react'
import { Route, Routes } from 'react-router-dom'

import RotaProtegida from '../components/RotaProtegida'
import { EsqueletoLista } from '../components/Esqueleto'
import LayoutPainel from '../layouts/LayoutPainel'
import LayoutPrincipal from '../layouts/LayoutPrincipal'
import Home from '../pages/Home'

// code splitting: só a home vem no primeiro carregamento
const Noticia = lazy(() => import('../pages/Noticia'))
const Categoria = lazy(() => import('../pages/Categoria'))
const Autor = lazy(() => import('../pages/Autor'))
const Busca = lazy(() => import('../pages/Busca'))
const Tendencias = lazy(() => import('../pages/Tendencias'))
const MaisLidas = lazy(() => import('../pages/MaisLidas'))
const Videos = lazy(() => import('../pages/Videos'))
const AoVivo = lazy(() => import('../pages/AoVivo'))
const Favoritos = lazy(() => import('../pages/Favoritos'))
const Historico = lazy(() => import('../pages/Historico'))
const Interesses = lazy(() => import('../pages/Interesses'))
const Entrar = lazy(() => import('../pages/Entrar'))
const Cadastrar = lazy(() => import('../pages/Cadastrar'))
const RecuperarSenha = lazy(() => import('../pages/RecuperarSenha'))
const RedefinirSenha = lazy(() => import('../pages/RedefinirSenha'))
const Perfil = lazy(() => import('../pages/Perfil'))
const NaoEncontrado = lazy(() => import('../pages/NaoEncontrado'))

const PainelVisaoGeral = lazy(() => import('../pages/admin/VisaoGeral'))
const PainelNoticias = lazy(() => import('../pages/admin/Noticias'))
const EditorNoticia = lazy(() => import('../pages/admin/EditorNoticia'))
const PainelUsuarios = lazy(() => import('../pages/admin/Usuarios'))
const PainelModeracao = lazy(() => import('../pages/admin/Moderacao'))
const PainelAoVivo = lazy(() => import('../pages/admin/AoVivo'))

function Carregando() {
  return (
    <div className="container" style={{ padding: '32px 16px' }}>
      <EsqueletoLista quantidade={6} />
    </div>
  )
}

export default function Rotas() {
  return (
    <Suspense fallback={<Carregando />}>
      <Routes>
        <Route element={<LayoutPrincipal />}>
          <Route index element={<Home />} />
          <Route path="noticia/:slug" element={<Noticia />} />
          <Route path="categoria/:slug" element={<Categoria />} />
          <Route path="autor/:username" element={<Autor />} />
          <Route path="busca" element={<Busca />} />
          <Route path="tendencias" element={<Tendencias />} />
          <Route path="mais-lidas" element={<MaisLidas />} />
          <Route path="videos" element={<Videos />} />
          <Route path="ao-vivo" element={<AoVivo />} />
          <Route path="ao-vivo/:slug" element={<AoVivo />} />
          <Route path="entrar" element={<Entrar />} />
          <Route path="cadastrar" element={<Cadastrar />} />
          <Route path="recuperar-senha" element={<RecuperarSenha />} />
          <Route path="redefinir-senha" element={<RedefinirSenha />} />
          <Route
            path="meus-favoritos"
            element={<RotaProtegida><Favoritos /></RotaProtegida>}
          />
          <Route path="historico" element={<RotaProtegida><Historico /></RotaProtegida>} />
          <Route path="interesses" element={<RotaProtegida><Interesses /></RotaProtegida>} />
          <Route path="perfil" element={<RotaProtegida><Perfil /></RotaProtegida>} />
          <Route path="*" element={<NaoEncontrado />} />
        </Route>

        <Route
          path="/admin"
          element={<RotaProtegida exigeRedacao><LayoutPainel /></RotaProtegida>}
        >
          <Route index element={<PainelVisaoGeral />} />
          <Route path="noticias" element={<PainelNoticias />} />
          <Route path="noticias/nova" element={<EditorNoticia />} />
          <Route path="noticias/:slug/editar" element={<EditorNoticia />} />
          <Route path="ao-vivo" element={<PainelAoVivo />} />
          <Route path="moderacao" element={<PainelModeracao />} />
          <Route path="usuarios" element={<PainelUsuarios />} />
        </Route>
      </Routes>
    </Suspense>
  )
}
