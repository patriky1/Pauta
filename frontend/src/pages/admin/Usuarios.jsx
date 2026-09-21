import { useCallback, useState } from 'react'

import { Esqueleto } from '../../components/Esqueleto'
import { EstadoErro } from '../../components/Estado'
import { useAviso } from '../../contexts/AvisoContext'
import useDebounce from '../../hooks/useDebounce'
import useRequisicao from '../../hooks/useRequisicao'
import useSeo from '../../hooks/useSeo'
import { painel } from '../../services/painel'
import { FUNCOES } from '../../utils/constantes'
import { dataCurta } from '../../utils/formatar'

export default function Usuarios() {
  const [busca, setBusca] = useState('')
  const termo = useDebounce(busca, 350)
  const { mostrar } = useAviso()
  useSeo({ titulo: 'Usuários — painel' })

  const buscar = useCallback(() => painel.usuarios({ search: termo || undefined, page_size: 30 }), [termo])
  const { dados, carregando, erro, recarregar } = useRequisicao(buscar, [termo])

  const executar = async (promessa, mensagem) => {
    try {
      await promessa
      mostrar(mensagem)
      recarregar()
    } catch (falha) {
      mostrar(falha.mensagem || 'Não foi possível concluir.', 'erro')
    }
  }

  const lista = dados?.results || []

  return (
    <div>
      <div className="pagina__cabecalho">
        <div>
          <h1 className="titulo-pagina">Usuários</h1>
          <p className="pagina__descricao">Funções, acesso e bloqueios da plataforma.</p>
        </div>
      </div>

      <div className="campo">
        <label htmlFor="busca-usuarios">Buscar</label>
        <input id="busca-usuarios" value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Nome, usuário ou e-mail" />
      </div>

      {erro ? <EstadoErro mensagem={erro} aoTentarNovamente={recarregar} /> : null}
      {carregando ? <Esqueleto altura={200} /> : null}

      {lista.length ? (
        <div className="tabela-rolagem">
        <table className="tabela">
          <thead>
            <tr><th>Usuário</th><th>E-mail</th><th>Função</th><th>Desde</th><th>Situação</th><th>Ações</th></tr>
          </thead>
          <tbody>
            {lista.map((usuario) => (
              <tr key={usuario.id}>
                <td><strong style={{ fontWeight: 600 }}>{usuario.nome}</strong><br /><span style={{ color: 'var(--grafite)', fontSize: 'var(--t-xs)' }}>@{usuario.username}</span></td>
                <td>{usuario.email}</td>
                <td>
                  <select
                    value={usuario.tipo_usuario}
                    aria-label={`Função de ${usuario.nome}`}
                    onChange={(e) => executar(painel.alterarFuncao(usuario.id, e.target.value), 'Função atualizada.')}
                  >
                    {FUNCOES.map((funcao) => (
                      <option key={funcao.valor} value={funcao.valor}>{funcao.rotulo}</option>
                    ))}
                  </select>
                </td>
                <td>{dataCurta(usuario.date_joined)}</td>
                <td>
                  <span className={`etiqueta etiqueta--${usuario.is_active ? 'ativo' : 'bloqueado'}`}>{usuario.is_active ? 'Ativo' : 'Bloqueado'}</span>
                </td>
                <td>
                  {usuario.is_active ? (
                    <button
                      type="button"
                      className="botao botao--pequeno botao--contorno-perigo"
                      onClick={() => executar(painel.bloquear(usuario.id, 'Violação das regras'), 'Usuário bloqueado.')}
                    >
                      Bloquear
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="botao botao--pequeno"
                      onClick={() => executar(painel.desbloquear(usuario.id), 'Usuário liberado.')}
                    >
                      Desbloquear
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      ) : null}
    </div>
  )
}
