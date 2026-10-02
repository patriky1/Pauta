# Backend — Pauta API

Django 5 + Django REST Framework. Consulte o `README.md` na raiz para a instalação completa.

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_data
python manage.py coleta_exemplos          # regras e fontes de exemplo da coleta
python manage.py coleta_fontes            # fontes brasileiras confiáveis (ativas)
python manage.py createsuperuser
python manage.py runserver

# coleta automática (guia completo em ../COLETA.md)
celery -A config worker -l info --pool=solo   # Windows precisa do --pool=solo
celery -A config beat -l info
```

## Organização

```
config/           settings, urls, wsgi, asgi, celery (agenda da coleta)
apps/core/        modelo base, paginação, permissões, erros padronizados, sitemap/robots
apps/users/       usuário com papéis, JWT, perfil público de autor, gestão de usuários
apps/categories/  categorias e tags
apps/news/        notícias, fontes, mídias, ao vivo, vídeos, anúncios, busca, feed
apps/comments/    comentários encadeados, curtidas, denúncias
apps/interactions/ favoritos, histórico, follows
apps/notifications/ notificações e regras de disparo
apps/analytics/   eventos de audiência e dados do painel
apps/coleta/      fontes externas, leitura de RSS/Atom/JSON/API, categorização,
                  deduplicação, tarefas Celery, trava entre processos, logs de execução
```

## Papéis e permissões

| Papel | Pode |
|---|---|
| ADMIN | tudo, inclusive gerir usuários e moderar |
| EDITOR | criar/editar/publicar qualquer matéria, moderar |
| JORNALISTA | criar e editar as próprias matérias, tocar coberturas ao vivo |
| AUTOR | criar e editar as próprias matérias |
| USUARIO | comentar, curtir, favoritar, seguir, receber notificações |

## Testes

```bash
python manage.py test
python manage.py test apps.coleta     # só a coleta
```
