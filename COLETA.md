# Coleta automática de notícias

O Pauta busca notícias em fontes externas (RSS/Atom, JSON Feed ou APIs oficiais) a cada
**40 minutos**, grava no banco sem duplicar, escolhe a categoria sozinho e mostra as mais
recentes no **carrossel da página inicial**.

```
Celery Beat (relógio, a cada 40 min)
   └─► fila no Redis
         └─► Celery Worker ─► manage.py coletar_noticias ─► trava (1 coleta por vez)
                                  │
                                  ▼
                           baixa cada fonte ativa ─► lê o feed ─► valida/deduplica ─► categoriza
                                  │                                    │
                                  │  uma fonte com erro não para as     ▼
                                  │  outras; o erro fica registrado   grava/atualiza
                                  ▼                                   a notícia
                           Log (ExecucaoColeta)                         │
                                                                        ▼
                                              limpa o cache do carrossel ─► React atualiza
                                                                            (a cada 2 min)
```

---

## 1. Instalação (uma vez)

```bash
cd backend
pip install -r requirements.txt      # agora inclui requests, celery e redis
python manage.py migrate             # cria as tabelas da coleta e os campos novos da notícia
python manage.py coleta_exemplos     # regras de palavras-chave + 2 fontes da Agência Brasil (inativas)
python manage.py coleta_fontes       # 11 fontes brasileiras confiáveis, já ATIVAS (seção 2.1)
```

Os dois comandos podem ser rodados de novo sem problema: não duplicam nada e não alteram
fontes que você já editou ou desativou no painel. Ambos precisam de categorias cadastradas
(`seed_data` ou o painel).

### Redis

O Celery precisa de um "carteiro" para levar as tarefas do relógio (beat) até quem trabalha
(worker). Usamos o **Redis**.

- **Windows (desenvolvimento):** o jeito mais simples é o Docker Desktop:
  `docker run -d --name redis -p 6379:6379 redis:7`.
  Sem Docker, use o Memurai (compatível com Redis) ou o Redis dentro do WSL.
- **Linux (produção):** `sudo apt install redis-server`.

No `.env` do backend:

```env
REDIS_URL=redis://localhost:6379/1          # cache compartilhado (carrossel atualiza na hora)
CELERY_BROKER_URL=redis://localhost:6379/0  # fila do Celery
```

> Sem Redis você ainda consegue testar tudo com o comando manual
> `python manage.py coletar_noticias` (seção 4) — só não terá o agendamento automático.

---

## 2. Como cadastrar uma fonte (sem mexer no código)

Entre em **`/django-admin/` → Coleta → Fontes de notícias → Adicionar**.

| Campo | O que colocar |
|---|---|
| **Nome** | Como a fonte aparece no site ("Agência Brasil"). |
| **Site da fonte** | Página inicial do veículo (usada no crédito). |
| **URL do feed/API** | O endereço do RSS/Atom, do JSON Feed ou da API oficial. |
| **Tipo** | `RSS / Atom`, `JSON Feed` ou `API JSON (com mapeamento)`. |
| **Ativa** | Desmarque para pausar a fonte sem apagar nada. |
| **Categoria padrão** | Usada quando a notícia não se encaixa em nenhuma regra. |
| **Publicar automaticamente** | Desmarcado = as notícias entram como "Em revisão" para a redação aprovar. |
| **Importar conteúdo completo** | Só marque se a licença permitir republicar o texto inteiro (ex.: Creative Commons). Sem isso, importa apenas o resumo e o link para a matéria original. |
| **Buscar imagem na página original** | Quando o feed não traz foto, lê a `og:image` da página (respeitando o `robots.txt`). |
| **Itens por coleta** | Quantas notícias ler por vez (padrão 30). |

Depois de salvar, use a ação **"Sincronizar agora"** na lista de fontes para testar na hora.
A coluna **situação** mostra `ok`, `parcial` ou `erro (Nx)` — passe o mouse para ver o motivo.
O link **log** abre o histórico de execuções daquela fonte.

**Dica:** para descobrir o RSS de um site, procure por "RSS" no rodapé dele ou abra o
código-fonte da página e procure `application/rss+xml`.

### 2.1 Fontes brasileiras incluídas

`python manage.py coleta_fontes` cadastra os feeds RSS oficiais abaixo (lista em
`backend/apps/coleta/fontes_brasil.py`). `--inativas` cria desligadas; `--listar` só mostra.

| Fonte | Categoria padrão |
|---|---|
| Agência Brasil — Últimas notícias | Brasil |
| Agência Brasil — Economia | Economia |
| Agência Câmara de Notícias | Política |
| g1 — Últimas notícias | Brasil |
| g1 — Política / Economia / Mundo / Ciência e Saúde / Educação | a da editoria |
| Folha de S.Paulo — Em cima da hora | Brasil |
| BBC News Brasil | Mundo |

Todas importam **só o resumo**, com crédito e link para a matéria original. As agências
públicas (Agência Brasil, Agência Câmara) autorizam a reprodução com crédito; se quiser o
texto integral delas, marque "Importar conteúdo completo" depois de conferir os termos
atuais. Nos veículos comerciais, mantenha só o resumo. Se um veículo mudar o endereço do
feed, a fonte aparece com `erro (Nx)` no painel e as demais continuam normalmente.

### Fonte do tipo API JSON

Algumas fontes oferecem uma API em JSON em vez de RSS. Nesse caso preencha, na seção
"API JSON (opcional)":

- **Mapeamento da API** — onde está cada informação na resposta. Exemplo para uma API que
  responde `{"articles": [{"title": ..., "url": ..., "urlToImage": ...}]}`:

  ```json
  {"itens": "articles", "titulo": "title", "url": "url", "resumo": "description",
   "imagem": "urlToImage", "data": "publishedAt", "autor": "author", "id": "url"}
  ```

  Caminhos com ponto funcionam para dados aninhados: `"itens": "dados.noticias"`.
  `titulo` e `url` são obrigatórios.
- **Variável de ambiente da chave** — só o **nome** da variável (ex.: `NEWSAPI_KEY`).
  A chave em si vai no `.env` (`NEWSAPI_KEY=abc123`) e **nunca** fica no banco.
- **Como enviar a chave** — nome do parâmetro na URL (`apiKey`) ou `header:X-Api-Key`
  quando a API pede a chave no cabeçalho.

---

## 3. Categorias automáticas

Para cada notícia a coleta tenta, nesta ordem:

1. **Mapeamento da própria fonte** — "Esportes" no feed ➜ "Esportes" no site
   (edite dentro da fonte, na tabela "Mapeamentos de categoria").
2. **Mapeamento global** — vale para todas as fontes
   (`/django-admin/` → Coleta → Mapeamentos de categoria, com o campo *fonte* vazio).
3. **Nome igual** — se a categoria do feed tem o mesmo nome de uma categoria do site.
4. **Palavras-chave** — `/django-admin/` → Coleta → Regras de categorização.
   Palavras no título valem 3 pontos, no resumo 1 ponto; precisa de pelo menos 2 pontos
   (ajustável em `COLETA_PONTUACAO_MINIMA`).
5. **Categoria padrão** da fonte.

O motivo da escolha fica registrado no log da execução, o que ajuda a ajustar as regras.

---

## 4. Como funciona a coleta a cada 40 minutos

Três processos ficam rodando juntos com o Django:

| Processo | Comando | Papel |
|---|---|---|
| Django | `python manage.py runserver` | Site e API |
| Worker | `celery -A config worker -l info --pool=solo` | Executa a coleta |
| Beat | `celery -A config beat -l info` | "Relógio": dispara a coleta a cada 40 min |

> **No Windows o `--pool=solo` é obrigatório** no worker. No Linux ele pode ser omitido.
> O worker e o beat precisam do Redis rodando (seção 1). Sem ele, o log mostra
> `Cannot connect to redis://localhost:6379/0`; nesse caso, inicie o Redis ou use o
> `rodar_agendador` (abaixo).

Abra três terminais no VS Code (dentro de `backend/`, com o `venv` ativado) e rode um
comando em cada. O intervalo muda com `COLETA_INTERVALO_MINUTOS` no `.env`. Para não
precisar abrir os terminais toda vez, veja a seção 4.1.

A tarefa agendada executa o próprio comando `manage.py coletar_noticias`, então a coleta
automática e a manual são exatamente a mesma coisa.

O que acontece em cada rodada:

- **Uma rodada por vez:** uma trava impede duas coletas simultâneas em **qualquer**
  processo — worker, comando manual, cron, "Sincronizar agora" do painel e a API
  (que responde `409`). Com PostgreSQL ela usa um *advisory lock* do banco (vale até entre
  servidores); com outros bancos, uma trava de arquivo do sistema. Nos dois casos ela é
  liberada sozinha se o processo cair. Não depende mais do Redis. Ajuste com
  `COLETA_TRAVA_BACKEND` (`auto`, `banco`, `arquivo` ou `cache`) — use `cache` (com Redis)
  apenas se o banco estiver atrás de um PgBouncer em modo transação.
- **Só fontes ativas;** fontes desligadas no painel são puladas.
- **Dados inválidos são descartados:** item sem título, sem link http(s) ou com URL maior
  que o campo do banco é contado como "ignorado", sem virar erro.
- **Sem duplicatas:** a notícia é reconhecida pelo ID do feed, pela URL original
  (limpa de `utm_*`, `fbclid` etc.) ou por um hash do título + link. Rodar duas vezes seguidas
  não cria nada novo — a sincronização é idempotente.
- **Atualizações:** se a fonte corrigir a notícia, ela é atualizada — **exceto** se a redação
  já tiver editado a notícia no painel depois da importação.
- **Economia de banda:** usa `ETag`/`Last-Modified`; se o feed não mudou, nada é baixado.
- **Falhas isoladas:** se uma fonte cair, dar erro de formato ou demorar demais, ela é
  marcada com erro e as outras seguem normalmente.
- **Notícias antigas** (mais de `COLETA_IDADE_MAXIMA_DIAS`, padrão 7 dias) são ignoradas.
- **Logs:** cada rodada gera um registro em "Execuções da coleta"; os registros com mais de
  30 dias são apagados sozinhos (`COLETA_RETENCAO_LOGS_DIAS`).
- **Carrossel:** quando entra notícia nova, o cache do carrossel é limpo. A página inicial
  confere a cada 2 minutos (e quando o leitor volta para a aba) e mostra as novidades sem
  recarregar a página.

### 4.1 Iniciar junto com o sistema e sobreviver a reinicializações

O beat guarda a hora da última execução em `CELERY_BEAT_SCHEDULE_FILENAME`
(padrão `backend/celerybeat-schedule`). Depois de reiniciar, ele continua do ponto certo e,
se o horário já passou, coleta na hora. No **primeiro** start (sem esse arquivo), ele
confere o log da coleta: se a última foi há mais de 40 minutos, já coleta ao subir em vez de
esperar o intervalo inteiro (`COLETA_EXECUTAR_AO_INICIAR=False` desliga isso).

Para os processos subirem sozinhos, escolha uma opção:

- **Docker (Linux, Windows ou macOS):** na raiz do projeto, `docker compose up -d --build`
  sobe PostgreSQL, Redis, API (porta 8000), worker e beat com `restart: unless-stopped`.
  Basta o Docker iniciar com o sistema (`sudo systemctl enable docker` no Linux; no Docker
  Desktop, "Start Docker Desktop when you sign in"). A agenda do beat fica num volume, e as
  migrações e as fontes brasileiras são aplicadas a cada `up`. Requer Docker Compose 2.24+.
  Acompanhe com `docker compose logs -f worker beat`.
- **Linux sem Docker (systemd):** use os arquivos prontos de `deploy/systemd/`
  (seção 7).

### Windows sem Redis: `rodar_agendador`

Para desenvolvimento no Windows, onde instalar o Redis e abrir worker + beat é trabalhoso,
use um único comando, que dispensa Redis e Celery:

```bash
python manage.py rodar_agendador                  # coleta ao iniciar e a cada 40 min
python manage.py rodar_agendador --intervalo 10   # a cada 10 min (para testar)
```

Deixe-o aberto num terminal ao lado do `runserver`. Ele executa o mesmo código de
`coletar_noticias` (mesma trava, deduplicação e logs). Se a coleta falhar, ele registra o
erro e tenta de novo no próximo ciclo. Ctrl+C encerra. Ele só roda enquanto o terminal
estiver aberto; para iniciar com o sistema e em produção, use o Celery (seção 4.1).
Não rode ele junto com o `celery beat`.

### Sem Celery? Use o agendador do sistema

O comando manual faz exatamente a mesma coleta:

```bash
python manage.py coletar_noticias                         # todas as fontes ativas
python manage.py coletar_noticias --fonte agencia-brasil  # só uma fonte (slug ou id)
```

- **Linux (cron):** `*/40 * * * * cd /srv/pauta/backend && venv/bin/python manage.py coletar_noticias`
- **Windows:** Agendador de Tarefas ➜ criar tarefa ➜ repetir a cada 40 minutos ➜
  programa `C:\caminho\backend\venv\Scripts\python.exe`, argumentos
  `manage.py coletar_noticias`, "iniciar em" `C:\caminho\backend`.

---

## 5. Como testar manualmente

1. `python manage.py coleta_exemplos --ativar`
2. `python manage.py coletar_noticias` — deve listar cada fonte com "novas N".
3. Rode o mesmo comando de novo — agora deve aparecer "novas 0" (sem duplicatas).
4. Abra `http://localhost:8000/api/news/?origem=importada` — só notícias importadas, cada
   uma com o bloco `origem` (fonte + URL original).
5. `http://localhost:8000/api/news/carrossel/` — as notícias do carrossel.
6. Abra o site (`npm run dev`) — o carrossel aparece no topo da home; clique numa notícia
   importada e confira, no fim da matéria, o crédito e o botão "Ler a matéria completa".
7. **Falha de fonte:** cadastre uma fonte com URL inexistente, clique em "Sincronizar agora"
   e veja a situação `erro (1x)` e o motivo — as outras fontes continuam funcionando.
8. **Agendamento:** com Redis, worker e beat rodando, coloque `COLETA_INTERVALO_MINUTOS=1`
   no `.env`, reinicie o beat e acompanhe os logs do worker. Volte para 40 depois.
9. **Concorrência:** com uma coleta em andamento (uma fonte lenta ajuda), rode
   `python manage.py coletar_noticias` em outro terminal — ele deve responder
   "Outra coleta já está em andamento." sem coletar nada.

### Faixa "Urgente" automática

A faixa vermelha no topo do site mostra, em rotação, até 5 notícias: primeiro as **marcadas
como urgentes** no painel (como sempre) e, se sobrar espaço, as **últimas notícias
publicadas** nas últimas 6 horas, inclusive as importadas pela coleta. Ela é calculada na
hora: não marca nenhuma notícia como urgente no banco nem dispara notificação de urgente
para os leitores. O React confere a faixa a cada 2 minutos, então as notícias de cada
coleta aparecem sem recarregar a página. No `.env`:

```env
URGENTE_AUTOMATICO=True     # False = só as marcadas manualmente
URGENTE_JANELA_HORAS=6      # só entram notícias publicadas nas últimas N horas
URGENTE_MAXIMO=5            # quantas aparecem na faixa
```

### Fotos das notícias

A foto é procurada nesta ordem: campos padrão do feed (`media:content`, `enclosure`...),
tags próprias como `<imagem-destaque>` (Agência Brasil) e, por último, as imagens dentro do
texto. **Logos, ícones SVG, pixels de rastreamento e imagens de "carregando" são descartados**,
para o logo do veículo nunca aparecer como se fosse a foto da matéria. Se nada sobrar, a
notícia fica sem foto (e não entra no carrossel, que só mostra notícias com imagem).

Se notícias já importadas ficaram com o logo, corrija com:

```bash
python manage.py coleta_reparar_imagens                   # todas as fontes
python manage.py coleta_reparar_imagens --fonte agencia-brasil
```

O comando busca a foto real no feed, e remove o logo das notícias que já saíram do feed.
Notícias com foto de verdade não são alteradas.

### Testes automatizados

```bash
cd backend
python manage.py test apps.coleta          # coleta, duplicidade, categorização, falhas,
                                           # API, filtros, carrossel, tarefa agendada,
                                           # trava entre processos e fontes brasileiras
python manage.py makemigrations --check --dry-run   # deve dizer "No changes detected"

cd ../frontend
npm test                                   # inclui os testes do carrossel
```

---

## 6. API

| Endpoint | Para quê |
|---|---|
| `GET /api/news/` | Notícias com paginação (`?page=`, `?page_size=`), ordenação (`?ordering=-data_publicacao`) e filtros: `categoria`, `tag`, `autor`, `desde`, `ate`, `destaque`, `fonte=<slug>`, `origem=importada\|redacao`, `search` |
| `GET /api/news/carrossel/?limite=6` | Notícias do carrossel (1 a 10) |
| `GET /api/news/destaques/` | Manchete + secundárias (coluna "Em destaque") |
| `GET /api/categories/` | Categorias |
| `/api/coleta/fontes/` | Cadastro de fontes (somente administradores); `POST /api/coleta/fontes/{id}/sincronizar/` |
| `/api/coleta/execucoes/`, `/mapeamentos/`, `/regras/` | Logs, mapeamentos e regras (somente administradores) |

---

## 7. Produção

`.env`:

```env
DEBUG=False
REDIS_URL=redis://127.0.0.1:6379/1
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
COLETA_LOG_ARQUIVO=/var/log/pauta/coleta.log   # opcional, com rotação automática
```

Rode **um** worker e **um** beat além do gunicorn. Com Docker, o `docker-compose.yml` da
raiz já faz isso (seção 4.1). Sem Docker, use as units prontas de `deploy/systemd/`
(`pauta-celery.service` e `pauta-beat.service`, com `Restart=always` e
`WantedBy=multi-user.target`, ou seja, sobem no boot e voltam se caírem). Ajuste `User` e
os caminhos `/srv/pauta/...` e então:

```bash
sudo cp deploy/systemd/pauta-*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pauta-celery pauta-beat
sudo journalctl -u pauta-celery -f        # acompanhar a coleta
```

> Nunca rode dois beats ao mesmo tempo (a coleta seria disparada em dobro — a trava descarta
> a segunda, mas é desperdício). Em hospedagens que não permitem processos extras, use o cron
> da seção 4.

---

## 8. Direitos e boas práticas

- Toda notícia importada guarda **fonte, autor original e URL original**, exibidos no cartão,
  no carrossel e na matéria, com link para o site de origem.
- Por padrão só o **resumo** é importado. O texto completo depende da licença da fonte.
- As imagens são exibidas pela URL original (não são copiadas para o servidor), com crédito.
- Não há scraping de conteúdo, nem tentativa de contornar paywall, CAPTCHA ou bloqueios.
  A única leitura de página é a `og:image` opcional, e só quando o `robots.txt` permite.
- O robô se identifica (`COLETA_USER_AGENT`) e não acessa endereços da rede interna.
- Prefira **desativar** uma fonte a apagá-la: apagar não remove as notícias já importadas,
  mas elas perdem o vínculo com a fonte.
