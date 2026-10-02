from rest_framework import serializers

from apps.users.serializers import UsuarioResumoSerializer

from .models import Comentario, Denuncia


class ComentarioSerializer(serializers.ModelSerializer):
    autor = UsuarioResumoSerializer(read_only=True)
    total_curtidas = serializers.IntegerField(read_only=True)
    curtido = serializers.SerializerMethodField()
    respostas = serializers.SerializerMethodField()

    class Meta:
        model = Comentario
        fields = ("id", "noticia", "autor", "resposta_a", "conteudo", "status",
                  "editado", "criado_em", "total_curtidas", "curtido", "respostas")
        read_only_fields = ("id", "autor", "status", "editado", "criado_em")

    def get_curtido(self, obj):
        usuario = self.context.get("request").user if self.context.get("request") else None
        if not usuario or not usuario.is_authenticated:
            return False
        return obj.curtidas.filter(usuario=usuario).exists()

    def get_respostas(self, obj):
        if obj.resposta_a_id:
            return []
        filhos = obj.respostas.filter(status=Comentario.Status.PUBLICADO).select_related("autor")
        return ComentarioSerializer(filhos, many=True, context=self.context).data

    def create(self, dados):
        dados["autor"] = self.context["request"].user
        return super().create(dados)

    def update(self, instancia, dados):
        instancia.conteudo = dados.get("conteudo", instancia.conteudo)
        instancia.editado = True
        instancia.save(update_fields=["conteudo", "editado", "atualizado_em"])
        return instancia


class DenunciaSerializer(serializers.ModelSerializer):
    usuario = UsuarioResumoSerializer(read_only=True)
    comentario_conteudo = serializers.CharField(source="comentario.conteudo", read_only=True)

    class Meta:
        model = Denuncia
        fields = ("id", "comentario", "comentario_conteudo", "usuario", "motivo",
                  "descricao", "status", "criado_em")
        read_only_fields = ("id", "usuario", "status", "criado_em")

    def create(self, dados):
        dados["usuario"] = self.context["request"].user
        return super().create(dados)
