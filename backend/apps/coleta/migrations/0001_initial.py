# Generated for Django 5.0.9 on 2026-09-29

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('categories', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FonteNoticia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criado_em', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='criado em')),
                ('atualizado_em', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('nome', models.CharField(max_length=120, unique=True, verbose_name='nome')),
                ('slug', models.SlugField(blank=True, max_length=140, unique=True, verbose_name='slug')),
                ('url_site', models.URLField(blank=True, max_length=500, verbose_name='site da fonte')),
                ('url_feed', models.URLField(help_text='Endereco do RSS/Atom, JSON Feed ou da API oficial.', max_length=1000, unique=True, verbose_name='URL do feed/API')),
                ('tipo', models.CharField(choices=[('RSS', 'RSS / Atom'), ('JSON_FEED', 'JSON Feed'), ('API_JSON', 'API JSON (com mapeamento)')], default='RSS', max_length=10, verbose_name='tipo')),
                ('ativa', models.BooleanField(db_index=True, default=True, verbose_name='ativa')),
                ('publicar_automaticamente', models.BooleanField(default=True, help_text="Desmarque para que as notícias entrem como 'Em revisão' no painel.", verbose_name='publicar automaticamente')),
                ('importar_conteudo_completo', models.BooleanField(default=False, help_text='Marque apenas se a licença da fonte permitir republicar o texto integral (ex.: Creative Commons). Caso contrário, só o resumo é importado.', verbose_name='importar conteudo completo')),
                ('buscar_imagem_na_pagina', models.BooleanField(default=False, help_text='Quando o feed não traz imagem, lê a og:image da página (respeita robots.txt).', verbose_name='buscar imagem na pagina original')),
                ('limite_por_coleta', models.PositiveSmallIntegerField(default=30, verbose_name='itens por coleta')),
                ('mapeamento_json', models.JSONField(blank=True, default=dict, help_text='Somente para "API JSON". Ex.: {"itens": "articles", "titulo": "title", "url": "url", "resumo": "description", "imagem": "urlToImage", "data": "publishedAt", "autor": "author", "id": "url"}', verbose_name='mapeamento da API')),
                ('chave_api_variavel', models.CharField(blank=True, help_text='NOME da variável do .env com a chave (ex.: NEWSAPI_KEY). A chave em si nunca fica no banco.', max_length=80, verbose_name='variavel de ambiente da chave')),
                ('chave_api_parametro', models.CharField(blank=True, help_text="Nome do parâmetro na URL (ex.: apiKey) ou 'header:Nome-Do-Cabecalho'.", max_length=80, verbose_name='como enviar a chave')),
                ('ultima_sincronizacao', models.DateTimeField(blank=True, null=True, verbose_name='ultima sincronizacao')),
                ('ultimo_sucesso', models.DateTimeField(blank=True, null=True, verbose_name='ultimo sucesso')),
                ('ultimo_erro', models.TextField(blank=True, verbose_name='ultimo erro')),
                ('erros_consecutivos', models.PositiveIntegerField(default=0, verbose_name='erros consecutivos')),
                ('total_importadas', models.PositiveIntegerField(default=0, verbose_name='total importadas')),
                ('etag', models.CharField(blank=True, max_length=255, verbose_name='ETag')),
                ('ultima_modificacao', models.CharField(blank=True, max_length=100, verbose_name='Last-Modified')),
                ('categoria_padrao', models.ForeignKey(help_text='Usada quando nenhum mapeamento ou palavra-chave identifica a categoria.', on_delete=django.db.models.deletion.PROTECT, related_name='fontes_externas', to='categories.categoria', verbose_name='categoria padrao')),
            ],
            options={
                'verbose_name': 'fonte de noticias',
                'verbose_name_plural': 'fontes de noticias',
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='RegraCategorizacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('palavras_chave', models.TextField(help_text='Separe por vírgula ou uma por linha. Ex.: inflação, juros, IPCA, Banco Central', verbose_name='palavras-chave')),
                ('peso', models.PositiveSmallIntegerField(default=1, verbose_name='peso')),
                ('ativa', models.BooleanField(default=True, verbose_name='ativa')),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='regras_coleta', to='categories.categoria', verbose_name='categoria')),
            ],
            options={
                'verbose_name': 'regra de categorizacao',
                'verbose_name_plural': 'regras de categorizacao',
                'ordering': ['categoria__nome'],
            },
        ),
        migrations.CreateModel(
            name='ExecucaoColeta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('EM_ANDAMENTO', 'Em andamento'), ('SUCESSO', 'Sucesso'), ('PARCIAL', 'Sucesso com erros'), ('ERRO', 'Erro')], db_index=True, default='EM_ANDAMENTO', max_length=12, verbose_name='status')),
                ('iniciada_em', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='iniciada em')),
                ('finalizada_em', models.DateTimeField(blank=True, null=True, verbose_name='finalizada em')),
                ('itens_lidos', models.PositiveIntegerField(default=0, verbose_name='itens lidos')),
                ('novas', models.PositiveIntegerField(default=0, verbose_name='novas')),
                ('atualizadas', models.PositiveIntegerField(default=0, verbose_name='atualizadas')),
                ('ignoradas', models.PositiveIntegerField(default=0, verbose_name='ignoradas')),
                ('mensagem', models.TextField(blank=True, verbose_name='mensagem')),
                ('fonte', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='execucoes', to='coleta.fontenoticia', verbose_name='fonte')),
            ],
            options={
                'verbose_name': 'execucao da coleta',
                'verbose_name_plural': 'execucoes da coleta',
                'ordering': ['-iniciada_em'],
                'indexes': [models.Index(fields=['fonte', '-iniciada_em'], name='coleta_exec_fonte_data_idx')],
            },
        ),
        migrations.CreateModel(
            name='MapeamentoCategoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('termo_origem', models.CharField(help_text='Como aparece no feed. Maiúsculas e acentos são ignorados na comparação.', max_length=120, verbose_name='categoria na fonte')),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mapeamentos_coleta', to='categories.categoria', verbose_name='categoria no site')),
                ('fonte', models.ForeignKey(blank=True, help_text='Deixe vazio para valer para todas as fontes.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mapeamentos', to='coleta.fontenoticia', verbose_name='fonte')),
            ],
            options={
                'verbose_name': 'mapeamento de categoria',
                'verbose_name_plural': 'mapeamentos de categoria',
                'ordering': ['fonte__nome', 'termo_origem'],
                'constraints': [models.UniqueConstraint(fields=('fonte', 'termo_origem'), name='coleta_mapeamento_unico_por_fonte'), models.UniqueConstraint(condition=models.Q(('fonte__isnull', True)), fields=('termo_origem',), name='coleta_mapeamento_global_unico')],
            },
        ),
    ]
