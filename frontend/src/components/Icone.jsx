const CAMINHOS = {
  busca: 'M11 4a7 7 0 1 0 4.2 12.6l4.1 4.1 1.4-1.4-4.1-4.1A7 7 0 0 0 11 4Zm0 2a5 5 0 1 1 0 10 5 5 0 0 1 0-10Z',
  sino: 'M12 2a6 6 0 0 0-6 6v4l-2 3v1h16v-1l-2-3V8a6 6 0 0 0-6-6Zm0 20a2.5 2.5 0 0 0 2.5-2.5h-5A2.5 2.5 0 0 0 12 22Z',
  usuario: 'M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10Zm0 2c-4.4 0-8 2.5-8 5.5V22h16v-2.5c0-3-3.6-5.5-8-5.5Z',
  sol: 'M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10Zm0-13V1h0m0 22v-3m8-8h3M1 12h3m14.6-6.6 2.1-2.1M3.3 20.7l2.1-2.1m12.2 0 2.1 2.1M3.3 3.3l2.1 2.1',
  lua: 'M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z',
  menu: 'M3 6h18v2H3V6Zm0 5h18v2H3v-2Zm0 5h18v2H3v-2Z',
  fechar: 'M6.2 4.8 4.8 6.2 10.6 12l-5.8 5.8 1.4 1.4L12 13.4l5.8 5.8 1.4-1.4L13.4 12l5.8-5.8-1.4-1.4L12 10.6 6.2 4.8Z',
  marcador: 'M6 2h12v20l-6-4.5L6 22V2Z',
  marcadorVazio: 'M6 2h12v20l-6-4.5L6 22V2Zm2 2v14.1l4-3 4 3V4H8Z',
  coracao: 'M12 21S3 14.6 3 8.8A4.8 4.8 0 0 1 12 6a4.8 4.8 0 0 1 9 2.8C21 14.6 12 21 12 21Z',
  comentario: 'M4 3h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H8l-5 4V4a1 1 0 0 1 1-1Z',
  relogio: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm1 5h-2v6l5 3 1-1.7-4-2.3V7Z',
  olho: 'M12 5c-5 0-9 4.5-9 7s4 7 9 7 9-4.5 9-7-4-7-9-7Zm0 11a4 4 0 1 1 0-8 4 4 0 0 1 0 8Z',
  seta: 'M9 6l6 6-6 6',
  leitura: 'M4 4h6a3 3 0 0 1 2 1 3 3 0 0 1 2-1h6v15h-6a3 3 0 0 0-2 1 3 3 0 0 0-2-1H4V4Z',
  lixeira: 'M9 3h6l1 2h4v2H4V5h4l1-2ZM6 9h12l-1 12H7L6 9Z',
  raio: 'M13 2 4 14h6l-1 8 9-12h-6l1-8Z',
  compartilhar: 'M18 16a3 3 0 0 0-2.2 1l-6-3.4a3 3 0 0 0 0-1.2l6-3.4a3 3 0 1 0-1-1.7L8.8 9.7a3 3 0 1 0 0 4.6l6 3.4A3 3 0 1 0 18 16Z',
  video: 'M4 5h11a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Zm13 5 4-3v10l-4-3v-4Z',
  casa: 'M12 3 2 11h3v9h6v-6h2v6h6v-9h3L12 3Z',
  sair: 'M10 3h9a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-9v-2h9V5h-9V3Zm-1 5 1.4 1.4L8.8 11H16v2H8.8l1.6 1.6L9 16l-4-4 4-4Z',
  grafico: 'M4 20h16v2H2V2h2v18Zm3-3V9h3v8H7Zm5 0V4h3v13h-3Zm5 0v-5h3v5h-3Z',
}

export default function Icone({ nome, tamanho = 20, titulo, preenchido = true, ...resto }) {
  const caminho = CAMINHOS[nome]
  if (!caminho) return null
  const traco = nome === 'sol' || nome === 'seta'
  return (
    <svg
      width={tamanho}
      height={tamanho}
      viewBox="0 0 24 24"
      fill={traco || !preenchido ? 'none' : 'currentColor'}
      stroke={traco || !preenchido ? 'currentColor' : 'none'}
      strokeWidth={traco || !preenchido ? 2 : 0}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={titulo ? undefined : 'true'}
      role={titulo ? 'img' : undefined}
      focusable="false"
      {...resto}
    >
      {titulo ? <title>{titulo}</title> : null}
      <path d={caminho} fillRule="evenodd" clipRule="evenodd" />
    </svg>
  )
}
