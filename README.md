# Pauta — plataforma de notícias

Plataforma de notícias completa, com **frontend React (Vite)** e **backend Django + DRF**
separados, banco **PostgreSQL**, autenticação **JWT**, feed personalizado, cobertura ao vivo,
comentários encadeados, painel administrativo, PWA e **coleta automática de notícias
externas** (RSS/Atom/APIs a cada 40 minutos, com Celery) exibidas num carrossel na home.

```
React ─► Axios ─► API REST ─► Django REST Framework ─► Django ORM ─► PostgreSQL
                                                          ▲
Celery Beat (40 min) ─► Redis ─► Celery Worker ─► coleta de RSS/APIs
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
| Redis | 6 (só para a coleta agendada — veja `COLETA.md`) |

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
python manage.py migrate
python manage.py seed_data          # conteúdo fictício para avaliar a interface
python manage.py coleta_exemplos    # regras de categorização + fontes de exemplo (inativas)
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
REDIS_URL=             CELERY_BROKER_URL=redis://localhost:6379/0
COLETA_INTERVALO_MINUTOS=40   (demais COLETA_* no .env.example)
```

Nenhuma senha, chave ou token fica no código — tudo vem do `.env`.

### Coleta automática de notícias

Guia completo em **[`COLETA.md`](COLETA.md)** (cadastro de fontes, categorias, Celery no
Windows, testes e produção). Resumo:

```bash
python manage.py coletar_noticias                    # coleta agora, sem Celery
celery -A config worker -l info --pool=solo          # terminal 2 (Windows: --pool=solo)
celery -A config beat -l info                        # terminal 3 — dispara a cada 40 min
```

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
                                            # comentários, favoritos, permissões e coleta
cd frontend && npm test                     # componentes críticos, formatadores e carrossel
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
GET    /api/news/carrossel/?limite=6  GET  /api/news/?origem=importada|redacao&fonte=<slug>

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
/api/coleta/fontes/     fontes externas (+ {id}/sincronizar/) — só administradores
/api/coleta/execucoes/  /api/coleta/mapeamentos/  /api/coleta/regras/
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

**Coleta automática** — `apps/coleta/`: fontes RSS/Atom, JSON Feed e APIs JSON cadastradas no
admin, coleta a cada 40 min (Celery Beat), deduplicação por ID externo/URL/hash, categorização
por mapeamento e palavras-chave, falhas isoladas por fonte, logs de execução e crédito da
fonte original em todas as telas. Detalhes em `COLETA.md`.

**Frontend** — home com carrossel de manchetes (autoplay, setas, pontos, teclado, toque e
atualização automática) ao lado da coluna "Em destaque", abas de feed (Para você, Últimas, Mais lidas,
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
celery -A config worker -l info       # coleta (use systemd/supervisor — ver COLETA.md)
celery -A config beat -l info         # agendamento a cada 40 min (apenas UM beat)
```

Com Redis configurado (`REDIS_URL`), o cache fica compartilhado entre Django e Celery, e o
carrossel mostra as notícias importadas logo após cada coleta.

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

- As migrações vêm versionadas: basta `python manage.py migrate`. Depois de atualizar o
  código, confira com `python manage.py makemigrations --check --dry-run`.
- As notícias importadas são publicadas com a conta técnica `coleta-automatica` (sem senha,
  não faz login); na tela aparecem a fonte e o autor originais.
- O editor de conteúdo do painel aceita HTML simples digitado pela redação. Como o corpo da
  matéria é renderizado com `dangerouslySetInnerHTML`, mantenha a publicação restrita à
  equipe (já é, pelas permissões) ou plugue um editor WYSIWYG com sanitização antes de abrir
  o painel a terceiros.
- As imagens de demonstração vêm de `picsum.photos`. Nada no funcionamento depende delas:
  todo campo de imagem aceita upload local (`imagem_principal`) ou URL (`imagem_url`).
- Integração com YouTube/Vimeo está preparada no model `Video` (plataforma + `id_externo`),
  com o player incorporado já funcionando na página `/videos`.
