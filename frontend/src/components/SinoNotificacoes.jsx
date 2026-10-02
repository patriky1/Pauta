import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext'
import useIntervalo from '../hooks/useIntervalo'
import { social } from '../services/social'
import { tempoRelativo } from '../utils/formatar'
import Icone from './Icone'

export default function SinoNotificacoes() {
  const { autenticado } = useAuth()
  const [aberto, setAberto] = useState(false)
  const [itens, setItens] = useState([])
  const [carregando, setCarregando] = useState(false)
  const [naoLidas, setNaoLidas] = useState(0)
  const caixa = useRef(null)
  const local = useLocation()

  const atualizarContador = useCallback(() => {
    if (!autenticado || document.hidden) return
    social.contadorNotificacoes().then((dados) => setNaoLidas(dados.nao_lidas || 0)).catch(() => null)
  }, [autenticado])

  useEffect(() => { atualizarContador() }, [atualizarContador])
  useIntervalo(atualizarContador, autenticado ? 60000 : 0)
  useEffect(() => { setAberto(false) }, [local.pathname])

  useEffect(() => {
    if (!aberto) return undefined
    const fora = (evento) => {
      if (caixa.current && !caixa.current.contains(evento.target)) setAberto(false)
    }
    const tecla = (evento) => { if (evento.key === 'Escape') setAberto(false) }
    document.addEventListener('mousedown', fora)
    document.addEventListener('keydown', tecla)
    return () => {
      document.removeEventListener('mousedown', fora)
      document.removeEventListener('keydown', tecla)
    }
  }, [aberto])

  const abrir = async () => {
    const proximo = !aberto
    setAberto(proximo)
    if (!proximo) return
    setCarregando(true)
    try {
      const dados = await social.notificacoes({ page_size: 10 })
      setItens(dados.results || [])
      setNaoLidas(dados.nao_lidas ?? 0)
    } catch {
      setItens([])
    } finally {
      setCarregando(false)
    }
  }

  const lerTodas = async () => {
    try {
      await social.marcarTodasLidas()
      setItens((atuais) => atuais.map((item) => ({ ...item, lida: true })))
      setNaoLidas(0)
    } catch {
      /* mantém o estado atual */
    }
  }

  if (!autenticado) return null

  return (
    <div className="suspenso" ref={caixa}>
      <button
        type="button"
        className="icone-botao"
        onClick={abrir}
        aria-expanded={aberto}
        aria-haspopup="true"
        aria-label={`Notificações${naoLidas ? `, ${naoLidas} não lidas` : ''}`}
      >
        <Icone nome="sino" tamanho={19} />
        {naoLidas > 0 ? (
          <span className="icone-botao__contador">{naoLidas > 99 ? '99+' : naoLidas}</span>
        ) : null}
      </button>

      {aberto ? (
        <div className="suspenso__painel suspenso__painel--largo">
          <div className="suspenso__cabecalho">
            <strong style={{ fontSize: 'var(--t-sm)' }}>Notificações</strong>
            {naoLidas > 0 ? (
              <button type="button" className="botao botao--fantasma botao--pequeno" onClick={lerTodas}>
                Marcar todas como lidas
              </button>
            ) : null}
          </div>
          {carregando ? (
            <p style={{ padding: 10, fontSize: 'var(--t-sm)', color: 'var(--grafite)' }}>Carregando…</p>
          ) : itens.length === 0 ? (
            <p style={{ padding: 10, fontSize: 'var(--t-sm)', color: 'var(--grafite)' }}>
              Nada novo por enquanto. Siga editorias e autores para receber avisos.
            </p>
          ) : (
            itens.map((item) => (
              <Link
                key={item.id}
                to={item.url || '/'}
                className={`notificacao${item.lida ? '' : ' notificacao--nova'}`}
                onClick={() => {
                  if (!item.lida) {
                    social.marcarLida(item.id).catch(() => null)
                    setNaoLidas((n) => Math.max(0, n - 1))
                  }
                  setAberto(false)
                }}
              >
                <strong>{item.titulo}</strong>
                {item.mensagem ? <span>{item.mensagem}</span> : null}
                <time dateTime={item.criado_em}>{tempoRelativo(item.criado_em)}</time>
              </Link>
            ))
          )}
        </div>
      ) : null}
    </div>
  )
}
