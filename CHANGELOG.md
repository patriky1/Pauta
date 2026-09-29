# Changelog

## Coleta automática de notícias e carrossel na home

### Backend
- Novo app `apps/coleta`: cadastro de fontes (RSS/Atom, JSON Feed e API JSON com mapeamento)
  pelo `/django-admin/` e por `/api/coleta/` (somente administradores), com situação,
  último erro, erros consecutivos e log de cada execução.
- Coleta a cada 40 minutos com **Celery + Celery Beat** (`config/celery.py`), ou manual com
  `python manage.py coletar_noticias`. Trava contra execuções simultâneas; uma fonte com
  falha não interrompe as demais.
- Leitor de feeds próprio (RSS 2.0, RSS 1.0/RDF, Atom, JSON Feed, API JSON), com proteção
  contra XML malicioso, limite de tamanho, tempo máximo, `ETag`/`Last-Modified` e bloqueio
  de endereços da rede interna.
- Sem duplicatas: ID externo por fonte, URL original normalizada e hash do conteúdo, com
  restrições únicas no banco. Sincronização idempotente; atualizações da fonte não
  sobrescrevem edições feitas pela redação.
- Categorização automática: mapeamento por fonte, mapeamento global, nome igual,
  palavras-chave com pontuação e categoria padrão.
- Notícia ganhou `fonte_externa`, `url_original`, `id_externo`, `hash_conteudo` e
  `autor_original` (migração `news/0003`). A API devolve o bloco `origem` com o crédito.
- Novos filtros `?fonte=` e `?origem=importada|redacao`; novo endpoint
  `/api/news/carrossel/` com cache invalidado a cada importação.
- Cache em Redis quando `REDIS_URL` está definido; logs da coleta com arquivo rotativo
  opcional. Dependências novas: `requests`, `celery`, `redis`.
- Fotos: leitura da tag `<imagem-destaque>` (Agência Brasil) e descarte de logos, SVG, pixels
  de rastreamento e imagens de carregamento; `og:image` genérica também é ignorada.
  Novo comando `coleta_reparar_imagens` corrige notícias já importadas com o logo.
- Comando `coleta_exemplos`: regras de palavras-chave em português e fontes da Agência Brasil.

### Frontend
- A imagem grande do topo da home virou o **carrossel** `CarrosselNoticias`: imagem,
  categoria, título, resumo e fonte; autoplay de 6 s com pausa, setas, pontos com barra de
  progresso, teclado (← →) e arraste no celular. Pausa com o mouse em cima, com foco do
  teclado e com a aba em segundo plano; respeita "reduzir movimento".
- A home consulta o carrossel a cada 2 minutos e ao voltar para a aba, sem piscar e sem
  mudar o slide que o leitor está vendo.
- A coluna "Em destaque" não repete notícias que já estão no carrossel.
- Notícias importadas mostram a fonte original no cartão, no carrossel e na matéria, com o
  botão "Ler a matéria completa no site da fonte".
- `Imagem`: opção `carregamento` para antecipar o próximo slide.
- `CartaoNoticia`: link com `aria-label` do título (corrige o teste `CartaoNoticia.test.jsx`).

### Documentação
- Novo guia `COLETA.md`; `README.md` e `backend/README.md` atualizados.

---

# Revisão do frontend (versão anterior)

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
