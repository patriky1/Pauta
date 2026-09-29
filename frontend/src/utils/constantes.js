export const NOME_SITE = import.meta.env.VITE_SITE_NAME || 'Pauta'
export const URL_SITE = import.meta.env.VITE_SITE_URL || 'http://localhost:5173'

export const ABAS_FEED = [
  { chave: 'para-voce', rotulo: 'Para você' },
  { chave: 'ultimas', rotulo: 'Últimas' },
  { chave: 'mais-lidas', rotulo: 'Mais lidas' },
  { chave: 'tendencias', rotulo: 'Tendências' },
  { chave: 'seguindo', rotulo: 'Seguindo' },
]

export const STATUS_NOTICIA = [
  { valor: 'RASCUNHO', rotulo: 'Rascunho' },
  { valor: 'REVISAO', rotulo: 'Em revisão' },
  { valor: 'AGENDADA', rotulo: 'Agendada' },
  { valor: 'PUBLICADA', rotulo: 'Publicada' },
  { valor: 'ARQUIVADA', rotulo: 'Arquivada' },
]

export const FUNCOES = [
  { valor: 'ADMIN', rotulo: 'Administrador' },
  { valor: 'EDITOR', rotulo: 'Editor' },
  { valor: 'JORNALISTA', rotulo: 'Jornalista' },
  { valor: 'AUTOR', rotulo: 'Autor' },
  { valor: 'USUARIO', rotulo: 'Usuário' },
]

export const PAPEIS_REDACAO = ['ADMIN', 'EDITOR', 'JORNALISTA', 'AUTOR']
