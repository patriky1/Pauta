# Frontend — Pauta

React 18 + Vite + React Router + Axios. Consulte o `README.md` na raiz para a visão geral.

```bash
cp .env.example .env
npm install
npm run dev      # http://localhost:5173
npm run build
npm test
```

## Organização

```
src/
├── components/  Header, Footer, NewsCard, NewsHero, BreakingNews, Comment, SearchBar,
│                Notification, Modal, Toast, Skeleton, Pagination, ShareButtons, TrendingList…
├── pages/       home, matéria, categoria, autor, busca, tendências, mais lidas, vídeos,
│                ao vivo, favoritos, histórico, interesses, conta  (+ pages/admin/)
├── layouts/     LayoutPrincipal e LayoutPainel
├── services/    api (axios + refresh de token), autenticacao, noticias, social, painel
├── hooks/       useDebounce, useRequisicao, useListaPaginada, useSeo, useIntervalo
├── contexts/    AuthContext, TemaContext (dark mode), AvisoContext (toasts)
├── routes/      rotas com lazy loading e proteção por papel
└── styles/      tokens.css (design system), base.css, app.css
```

## Design

Tipografia: **Newsreader** (serifada, para manchetes e corpo de texto) e **IBM Plex Sans**
(interface). Vermelho é reservado ao que está acontecendo agora — urgente e ao vivo; azul-tinta
conduz a navegação. Todo o tema vive em `styles/tokens.css`, com variante escura automática.

Responsivo de 320px a 1920px; nenhum componente quebra nos pontos 320/375/390/430/768/1024/1366/1440/1920.
