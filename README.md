# Pauta — plataforma de notícias

Plataforma de notícias completa, com **frontend React (Vite)** e **backend Django + DRF**
separados, banco **PostgreSQL**, autenticação **JWT**, feed personalizado, cobertura ao vivo,
comentários encadeados, painel administrativo e PWA.

```
React ─► Axios ─► API REST ─► Django REST Framework ─► Django ORM ─► PostgreSQL
```

```
pauta/
├── backend/     Django 5 + DRF  (API em /api/)
└── frontend/    React 18 + Vite (SPA em /)
```

---

## 1. Requisitos

| Ferramenta | Versão mínima |
|---|---|
| Python | 3.11 |
| Node.js | 18 (recomendado 20+) |
| PostgreSQL | 14 |

> Sem PostgreSQL à mão? Coloque `DB_ENGINE=sqlite` no `.env` do backend e tudo roda igual,
> só trocando o banco.

---

## 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # e edite as credenciais do banco
```

Crie o banco no PostgreSQL (uma vez):

```sql
CREATE DATABASE pauta;
```

Migrações, dados de demonstração e servidor:

```bash
python manage.py makemigrations users categories news comments interactions notifications analytics
python manage.py migrate
python manage.py seed_data          # conteúdo fictício para avaliar a interface
python manage.py createsuperuser    # seu acesso ao /django-admin
python manage.py runserver
```

A API sobe em `http://localhost:8000/api/`.

**Acesso de demonstração criado pelo seed:** `admin` / `pauta12345`
(também existem `editor`, `jornalista`, `marcos`, `helena`, `rafael` e `leitor1`…`leitor12`,
todos com a mesma senha).

### Variáveis do `.env`

```env
SECRET_KEY=            DEBUG=True            ALLOWED_HOSTS=localhost,127.0.0.1
SITE_URL=http://localhost:5173               SITE_NAME=Pauta
DB_ENGINE=postgres     DB_NAME=              DB_USER=      DB_PASSWORD=
DB_HOST=localhost      DB_PORT=5432
CORS_ALLOWED_ORIGINS=http://localhost:5173
JWT_ACCESS_MINUTES=60  JWT_REFRESH_DAYS=7
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Nenhuma senha, chave ou token fica no código — tudo vem do `.env`.

---

## 3. Frontend

```bash
cd frontend
cp .env.example .env               # VITE_API_URL=http://localhost:8000/api
npm install
npm run dev                        # http://localhost:5173
```

Build de produção e pré-visualização:

```bash
npm run build
npm run preview
```

---

## 4. Testes

```bash
cd backend  && python manage.py test        # autenticação, notícias, categorias,
                                            # comentários, favoritos e permissões
cd frontend && npm test                     # componentes críticos e formatadores
```

---

## 5. Documentação da API

Com o backend rodando:

| Endereço | O que é |
|---|---|
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | ReDoc |
| `/api/schema/` | OpenAPI 3 (JSON) |
| `/django-admin/` | Django Admin |
| `/sitemap.xml`, `/robots.txt` | SEO |

### Principais endpoints

```
POST   /api/auth/register/            POST /api/auth/login/       POST /api/auth/refresh/
GET    /api/auth/me/                  POST /api/auth/password/reset/

GET    /api/news/                     GET  /api/news/{slug}/
GET    /api/news/latest/              GET  /api/news/most-read/?periodo=hoje|semana|mes
GET    /api/news/trending/            GET  /api/news/for-you/     GET /api/news/seguindo/
GET    /api/news/destaques/           GET  /api/news/breaking/

GET    /api/categories/               GET  /api/tags/
GET    /api/authors/                  GET  /api/authors/{username}/noticias/

GET    /api/comments/?noticia=1       POST /api/comments/{id}/curtir/
GET    /api/favorites/                GET  /api/history/
POST   /api/follow/categories|authors|tags/
GET    /api/notifications/            POST /api/notifications/ler-todas/
GET    /api/search/?q=&categoria=&autor=&tag=&desde=&ate=
GET    /api/live/                     GET  /api/videos/           GET /api/ads/?posicao=TOPO
POST   /api/analytics/                GET  /api/analytics/dashboard/

/api/admin/news/        CRUD editorial (+ publicar, arquivar, revisao, destacar, urgente)
/api/admin/users/       gestão de usuários (+ bloquear, desbloquear, funcao)
```

Os nomes dos campos seguem o modelo de dados em português (`titulo`, `resumo`, `conteudo`,
`data_publicacao`…) e são exatamente os mesmos consumidos pelo React.

---

## 6. O que está implementado

**Backend** — models completos (usuário com papéis ADMIN/EDITOR/JORNALISTA/AUTOR/USUARIO,
notícia com 5 status e 7 formatos, categorias, tags, fontes, mídias, cobertura ao vivo,
vídeos, anúncios, comentários encadeados, denúncias, favoritos, histórico, follows,
notificações, eventos de analytics), serializers, viewsets, permissões por papel, filtros,
busca avançada, paginação, throttling, JWT com refresh rotativo, recuperação de senha,
tratamento padronizado de erros (400/401/403/404/409/429/500), Swagger, sitemap e robots.

**Feed personalizado** — `apps/news/services.py` pontua cada matéria por categorias, autores
e tags seguidos, recência, destaque, urgência e audiência, penalizando o que já foi lido.
Trocar essa função por um serviço de IA não exige mudar nenhuma view.

**Frontend** — home com hero editorial, abas de feed (Para você, Últimas, Mais lidas,
Tendências, Seguindo), matéria com modo leitura, compartilhamento, comentários encadeados,
notícias relacionadas e Schema.org `NewsArticle`; páginas de categoria, autor, busca com
filtros e debounce, tendências, mais lidas, vídeos, ao vivo com atualização automática,
favoritos, histórico, interesses, perfil e autenticação completa; painel administrativo com
indicadores, gráfico de audiência, gestão de notícias, moderação, usuários e coberturas ao
vivo. Dark mode persistente, skeletons, estados de erro e vazio, code splitting, lazy loading
de imagens e PWA (manifest + service worker).

**Acessibilidade** — HTML semântico, `aria-label`, foco visível, navegação por teclado, link
para pular ao conteúdo, alt em imagens e `prefers-reduced-motion` respeitado.

---

## 7. Produção

**Backend**

```env
DEBUG=False
ALLOWED_HOSTS=seudominio.com
SECRET_KEY=<chave forte e única>
CORS_ALLOWED_ORIGINS=https://seudominio.com
```

```bash
python manage.py collectstatic
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

Com `DEBUG=False` o projeto liga HSTS, cookies seguros e redirecionamento HTTPS. Os arquivos
estáticos são servidos por WhiteNoise; o diretório `media/` deve ir para um storage externo
(S3, Spaces) em produção.

**Frontend**

```env
VITE_API_URL=https://api.seudominio.com/api
VITE_SITE_URL=https://seudominio.com
```

`npm run build` gera `dist/`, que pode ser publicado em qualquer host estático (Netlify,
Vercel, Nginx). Configure o servidor para devolver `index.html` em todas as rotas (SPA).

---

## 8. Observações honestas

- As migrações não vêm versionadas: rode `makemigrations` uma vez, como indicado acima.
  Isso evita conflito com o seu ambiente e é o fluxo normal em um projeto Django novo.
- O editor de conteúdo do painel aceita HTML simples digitado pela redação. Como o corpo da
  matéria é renderizado com `dangerouslySetInnerHTML`, mantenha a publicação restrita à
  equipe (já é, pelas permissões) ou plugue um editor WYSIWYG com sanitização antes de abrir
  o painel a terceiros.
- As imagens de demonstração vêm de `picsum.photos`. Nada no funcionamento depende delas:
  todo campo de imagem aceita upload local (`imagem_principal`) ou URL (`imagem_url`).
- Integração com YouTube/Vimeo está preparada no model `Video` (plataforma + `id_externo`),
  com o player incorporado já funcionando na página `/videos`.
