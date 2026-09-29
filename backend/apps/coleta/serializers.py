import re

from rest_framework import serializers

from apps.categories.serializers import CategoriaResumoSerializer
from apps.categories.models import Categoria

from .models import ExecucaoColeta, FonteNoticia, MapeamentoCategoria, RegraCategorizacao


class FonteNoticiaSerializer(serializers.ModelSerializer):
    categoria_padrao = CategoriaResumoSerializer(read_only=True)
    categoria_padrao_id = serializers.PrimaryKeyRelatedField(
        source="categoria_padrao", queryset=Categoria.objects.all(), write_only=True,
    )

    class Meta:
        model = FonteNoticia
        fields = (
            "id", "nome", "slug", "url_site", "url_feed", "tipo", "ativa",
            "categoria_padrao", "categoria_padrao_id", "publicar_automaticamente",
            "importar_conteudo_completo", "buscar_imagem_na_pagina", "limite_por_coleta",
            "mapeamento_json", "chave_api_variavel", "chave_api_parametro",
            "ultima_sincronizacao", "ultimo_sucesso", "ultimo_erro", "erros_consecutivos",
            "total_importadas", "criado_em",
        )
        read_only_fields = (
            "id", "slug", "ultima_sincronizacao", "ultimo_sucesso", "ultimo_erro",
            "erros_consecutivos", "total_importadas", "criado_em",
        )

    def validate_chave_api_variavel(self, valor):
        if valor and not re.fullmatch(r"[A-Z_][A-Z0-9_]*", valor):
            raise serializers.ValidationError(
                "Informe o NOME da variavel de ambiente (ex.: NEWSAPI_KEY), nao a chave.")
        return valor

    def validate_limite_por_coleta(self, valor):
        if not 1 <= valor <= 200:
            raise serializers.ValidationError("Use um valor entre 1 e 200.")
        return valor

    def validate(self, dados):
        tipo = dados.get("tipo", getattr(self.instance, "tipo", FonteNoticia.Tipo.RSS))
        mapeamento = dados.get("mapeamento_json", getattr(self.instance, "mapeamento_json", {}))
        if not isinstance(mapeamento, dict):
            raise serializers.ValidationError({"mapeamento_json": "Deve ser um objeto JSON."})
        if tipo == FonteNoticia.Tipo.API_JSON and not {"titulo", "url"} <= set(mapeamento):
            raise serializers.ValidationError(
                {"mapeamento_json": "Para API JSON informe ao menos 'titulo' e 'url'."})
        return dados


class ExecucaoColetaSerializer(serializers.ModelSerializer):
    fonte_nome = serializers.CharField(source="fonte.nome", read_only=True)

    class Meta:
        model = ExecucaoColeta
        fields = ("id", "fonte", "fonte_nome", "status", "iniciada_em", "finalizada_em",
                  "duracao_segundos", "itens_lidos", "novas", "atualizadas", "ignoradas",
                  "mensagem")
        read_only_fields = fields


class MapeamentoCategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapeamentoCategoria
        fields = ("id", "fonte", "termo_origem", "categoria")


class RegraCategorizacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegraCategorizacao
        fields = ("id", "categoria", "palavras_chave", "peso", "ativa")
