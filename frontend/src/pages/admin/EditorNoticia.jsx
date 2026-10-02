import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { EstadoErro } from '../../components/Estado'
import { useAviso } from '../../contexts/AvisoContext'
import useRequisicao from '../../hooks/useRequisicao'
import useSeo from '../../hooks/useSeo'
import { catalogo } from '../../services/noticias'
import { painel } from '../../services/painel'
import { STATUS_NOTICIA } from '../../utils/constantes'

const VAZIO = {
  titulo: '', subtitulo: '', resumo: '', conteudo: '', imagem_url: '',
  imagem_legenda: '', imagem_credito: '', categoria_id: '', tags: '',
  status: 'RASCUNHO', formato: 'TEXTO', destaque: false, breaking_news: false,
  exclusivo: false, permitir_comentarios: true, data_publicacao: '',
}

export default function EditorNoticia() {
  const { slug } = useParams()
  const navegar = useNavigate()
  const { mostrar } = useAviso()
  const [form, setForm] = useState(VAZIO)
  const [salvando, setSalvando] = useState(false)
  const [erroEnvio, setErroEnvio] = useState('')

  const { dados: categorias } = useRequisicao(() => catalogo.categorias(), [])
  const { dados: noticia, erro, recarregar } = useRequisicao(
    () => (slug ? painel.noticia(slug) : Promise.resolve(null)),
    [slug],
    { ativo: Boolean(slug) }
  )

  useSeo({ titulo: slug ? 'Editar notícia' : 'Nova notícia' })

  useEffect(() => {
    if (!noticia) return
    setForm({
      titulo: noticia.titulo || '',
      subtitulo: noticia.subtitulo || '',
      resumo: noticia.resumo || '',
      conteudo: noticia.conteudo || '',
      imagem_url: noticia.imagem || '',
      imagem_legenda: noticia.imagem_legenda || '',
      imagem_credito: noticia.imagem_credito || '',
      categoria_id: noticia.categoria?.id || '',
      tags: (noticia.tags || []).map((tag) => tag.nome).join(', '),
      status: noticia.status || 'RASCUNHO',
      formato: noticia.formato || 'TEXTO',
      destaque: noticia.destaque,
      breaking_news: noticia.breaking_news,
      exclusivo: noticia.exclusivo,
      permitir_comentarios: noticia.permitir_comentarios,
      data_publicacao: noticia.data_publicacao ? noticia.data_publicacao.slice(0, 16) : '',
    })
  }, [noticia])

  const trocar = (campo) => (evento) => {
    const valor = evento.target.type === 'checkbox' ? evento.target.checked : evento.target.value
    setForm((atual) => ({ ...atual, [campo]: valor }))
  }

  const enviar = async (evento) => {
    evento.preventDefault()
    setErroEnvio('')
    setSalvando(true)
    const carga = {
      ...form,
      categoria_id: Number(form.categoria_id),
      tags: form.tags.split(',').map((tag) => tag.trim()).filter(Boolean),
      data_publicacao: form.data_publicacao ? new Date(form.data_publicacao).toISOString() : null,
    }
    try {
      const salva = slug
        ? await painel.atualizarNoticia(slug, carga)
        : await painel.criarNoticia(carga)
      mostrar(slug ? 'Notícia atualizada.' : 'Notícia criada.')
      navegar(`/admin/noticias/${salva.slug}/editar`, { replace: true })
    } catch (falha) {
      setErroEnvio(falha.mensagem || 'Revise os campos destacados.')
    } finally {
      setSalvando(false)
    }
  }

  if (erro) return <EstadoErro mensagem={erro} aoTentarNovamente={recarregar} />

  return (
    <form onSubmit={enviar} className="formulario formulario--largo">
      <div className="pagina__cabecalho">
        <div>
          <h1 className="titulo-pagina">{slug ? 'Editar notícia' : 'Nova notícia'}</h1>
          <p className="pagina__descricao">Campos com título, conteúdo e editoria são obrigatórios.</p>
        </div>
        <div className="grupo-botoes">
          {slug && form.status === 'PUBLICADA' ? (
            <a className="botao" href={`/noticia/${slug}`} target="_blank" rel="noopener noreferrer">Ver no site</a>
          ) : null}
          <button type="submit" className="botao botao--primario" disabled={salvando}>
            {salvando ? 'Salvando…' : 'Salvar'}
          </button>
        </div>
      </div>

      {erroEnvio ? <div className="aviso" role="alert">{erroEnvio}</div> : null}

      <div className="coluna-dupla">
        <div className="bloco" style={{ minWidth: 0 }}>
          <div className="campo">
            <label htmlFor="titulo">Título</label>
            <input id="titulo" value={form.titulo} onChange={trocar('titulo')} required maxLength={200} />
          </div>
          <div className="campo">
            <label htmlFor="subtitulo">Subtítulo</label>
            <input id="subtitulo" value={form.subtitulo} onChange={trocar('subtitulo')} maxLength={300} />
          </div>
          <div className="campo">
            <label htmlFor="resumo">Resumo</label>
            <textarea id="resumo" value={form.resumo} onChange={trocar('resumo')} maxLength={500} style={{ minHeight: 80 }} />
          </div>
          <div className="campo">
            <label htmlFor="conteudo">Conteúdo</label>
            <span className="campo__ajuda">Aceita HTML simples: &lt;p&gt;, &lt;h2&gt;, &lt;strong&gt;, &lt;em&gt;, &lt;ul&gt;, &lt;blockquote&gt;.</span>
            <textarea id="conteudo" value={form.conteudo} onChange={trocar('conteudo')} required style={{ minHeight: 340, fontFamily: 'ui-monospace, monospace' }} />
          </div>
        </div>

        <aside className="lateral bloco" style={{ gap: 0 }}>
          <div className="campo">
            <label htmlFor="categoria">Categoria</label>
            <select id="categoria" value={form.categoria_id} onChange={trocar('categoria_id')} required>
              <option value="">Selecione</option>
              {(categorias || []).map((categoria) => (
                <option key={categoria.id} value={categoria.id}>{categoria.nome}</option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="tags">Tags (separadas por vírgula)</label>
            <input id="tags" value={form.tags} onChange={trocar('tags')} />
          </div>
          <div className="campo">
            <label htmlFor="status">Status</label>
            <select id="status" value={form.status} onChange={trocar('status')}>
              {STATUS_NOTICIA.map((item) => (
                <option key={item.valor} value={item.valor}>{item.rotulo}</option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label htmlFor="data">Publicar em</label>
            <input id="data" type="datetime-local" value={form.data_publicacao} onChange={trocar('data_publicacao')} />
          </div>
          <div className="campo">
            <label htmlFor="formato">Formato</label>
            <select id="formato" value={form.formato} onChange={trocar('formato')}>
              <option value="TEXTO">Matéria</option>
              <option value="GALERIA">Galeria</option>
              <option value="VIDEO">Vídeo</option>
              <option value="AUDIO">Áudio</option>
              <option value="PODCAST">Podcast</option>
              <option value="INFOGRAFICO">Infográfico</option>
              <option value="AO_VIVO">Cobertura ao vivo</option>
            </select>
          </div>
          <div className="campo">
            <label htmlFor="imagem">Imagem principal (URL)</label>
            <input id="imagem" value={form.imagem_url} onChange={trocar('imagem_url')} placeholder="https://" />
          </div>
          <div className="campo">
            <label htmlFor="legenda">Legenda da imagem</label>
            <input id="legenda" value={form.imagem_legenda} onChange={trocar('imagem_legenda')} />
          </div>
          <div className="campo">
            <label htmlFor="credito">Crédito da imagem</label>
            <input id="credito" value={form.imagem_credito} onChange={trocar('imagem_credito')} />
          </div>

          <fieldset style={{ border: '1px solid var(--borda)', borderRadius: 8, padding: 12, margin: 0 }}>
            <legend style={{ fontSize: 'var(--t-sm)' }}>Sinalizações</legend>
            {[
              ['destaque', 'Destacar na home'],
              ['breaking_news', 'Marcar como urgente'],
              ['exclusivo', 'Conteúdo exclusivo'],
              ['permitir_comentarios', 'Permitir comentários'],
            ].map(([campo, rotulo]) => (
              <label key={campo} className="caixa-selecao">
                <input type="checkbox" checked={Boolean(form[campo])} onChange={trocar(campo)} />
                {rotulo}
              </label>
            ))}
          </fieldset>
        </aside>
      </div>
    </form>
  )
}
