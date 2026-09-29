# Generated for Django 5.0.9 on 2026-09-29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coleta', '0001_initial'),
        ('news', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='noticia',
            name='imagem_url',
            field=models.URLField(blank=True, max_length=1000, verbose_name='imagem por URL'),
        ),
        migrations.AddField(
            model_name='noticia',
            name='fonte_externa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='noticias', to='coleta.fontenoticia', verbose_name='fonte externa'),
        ),
        migrations.AddField(
            model_name='noticia',
            name='url_original',
            field=models.URLField(blank=True, db_index=True, max_length=1000, verbose_name='URL original'),
        ),
        migrations.AddField(
            model_name='noticia',
            name='id_externo',
            field=models.CharField(blank=True, max_length=500, verbose_name='identificador externo'),
        ),
        migrations.AddField(
            model_name='noticia',
            name='hash_conteudo',
            field=models.CharField(blank=True, db_index=True, max_length=64, verbose_name='hash de deduplicacao'),
        ),
        migrations.AddField(
            model_name='noticia',
            name='autor_original',
            field=models.CharField(blank=True, max_length=200, verbose_name='autor na fonte'),
        ),
        migrations.AddConstraint(
            model_name='noticia',
            constraint=models.UniqueConstraint(condition=models.Q(('id_externo', ''), _negated=True), fields=('fonte_externa', 'id_externo'), name='noticia_id_externo_unico_por_fonte'),
        ),
        migrations.AddConstraint(
            model_name='noticia',
            constraint=models.UniqueConstraint(condition=models.Q(('url_original', ''), _negated=True), fields=('url_original',), name='noticia_url_original_unica'),
        ),
    ]
