# Changelog — revisão do frontend

## Correções de bugs
- **Carregamento infinito em desenvolvimento**: `useRequisicao` agora é compatível com a montagem dupla do StrictMode e ignora respostas fora de ordem.
- **Gaveta do menu presa no cabeçalho**: o `backdrop-filter` do cabeçalho prendia o `position: fixed`; a gaveta agora é renderizada via portal no `body`.
- **Cartões horizontais quebrados** em "Mais lidas hoje", salvos e histórico.
- **Datas com um dia a menos** no fuso do Brasil (datas "AAAA-MM-DD" eram lidas como UTC).
- **"Ao vivo" piscava** o carregamento a cada 30s; agora atualiza em silêncio e só com a cobertura no ar.
- **Busca do cabeçalho ignorada** quando já se estava na página `/busca`.
- `useListaPaginada` protegido contra respostas fora de ordem ao trocar de aba.
- `useSeo` não recria o Schema.org a cada renderização.
- Aba de moderação renomeada para "Comentários recentes", o que ela de fato mostra.
- Tratamento de erro em interesses, favoritos, histórico, curtidas e denúncias.
- Categorias com cache de 5 minutos (cabeçalho, rodapé e filtros faziam requisições repetidas).
- Aviso do React sobre `fetchpriority` resolvido de forma compatível com React 18 e 19.

## Interface
- Cabeçalho em duas linhas: busca central e seções + editorias roláveis.
- Menu suspenso de conta e notificações com fechamento por clique fora e Esc.
- Navegação inferior no celular (Início, Buscar, Ao vivo, Salvos, Conta).
- Feed no celular: primeira matéria em destaque e as demais em lista com miniatura.
- Tipografia fluida (`clamp`) de 320px a 1440px.
- Componente `Imagem` com proporção reservada e reserva visual quando a URL falha.
- Barra de progresso de leitura na matéria.
- `LimiteErro`: uma falha de renderização não deixa mais a tela branca.
- Formulários de autenticação em cartão; perfil, busca e painel organizados em blocos.
- Painel: tabelas com rolagem interna, status coloridos, indicadores em grade responsiva e menu horizontal no celular.
- Contraste da faixa "Urgente" no modo escuro; campos em 16px no celular para o iOS não dar zoom; modais em formato de folha no celular.

## Novos arquivos
- `src/components/Imagem.jsx`, `NavegacaoInferior.jsx`, `LimiteErro.jsx`, `MenuUsuario.jsx`
- `src/hooks/useMidia.js`

## Validação
Compilado com esbuild e renderizado no Chromium (Playwright) com API simulada em 320, 375, 390, 768, 1024, 1280 e 1440px, temas claro e escuro, logado e deslogado: sem transbordo horizontal e sem erros de JavaScript.
