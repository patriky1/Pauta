import { Outlet, useLocation } from 'react-router-dom'

import BarraUrgente from '../components/BarraUrgente'
import Cabecalho from '../components/Cabecalho'
import LimiteErro from '../components/LimiteErro'
import NavegacaoInferior from '../components/NavegacaoInferior'
import Rodape from '../components/Rodape'

export default function LayoutPrincipal() {
  const { pathname } = useLocation()

  return (
    <>
      <a className="pular-para-conteudo" href="#conteudo">Pular para o conteúdo</a>
      <Cabecalho />
      <BarraUrgente />
      <main id="conteudo">
        <LimiteErro chave={pathname}>
          <Outlet />
        </LimiteErro>
      </main>
      <Rodape />
      <NavegacaoInferior />
    </>
  )
}
