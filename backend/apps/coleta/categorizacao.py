"""Escolha automatica de categoria para uma noticia importada.

Ordem de decisao (a primeira que responder vence):
1. mapeamento cadastrado para a fonte   ("Politica & Governo" -> Politica)
2. mapeamento global                     (vale para todas as fontes)
3. categoria do feed com o mesmo nome de uma categoria do site
4. palavras-chave no titulo (peso 3) e no resumo (peso 1)
5. categoria padrao da fonte

Modulo sem dependencia do Django: recebe dados simples ja carregados do banco.
"""
import re
from dataclasses import dataclass, field

from .texto import normalizar_texto

PESO_TITULO = 3
PESO_RESUMO = 1


def separar_termos(texto):
    """'a, b\\nc' -> ['a', 'b', 'c'] ja normalizados."""
    termos = []
    for bruto in re.split(r"[,;\n]+", texto or ""):
        termo = normalizar_texto(bruto)
        if termo and termo not in termos:
            termos.append(termo)
    return termos


def _padrao(termo):
    return re.compile(r"(?<![a-z0-9])" + re.escape(termo) + r"(?![a-z0-9])")


@dataclass
class Categorizador:
    categoria_padrao: int
    mapeamentos_fonte: dict = field(default_factory=dict)    # termo normalizado -> id
    mapeamentos_globais: dict = field(default_factory=dict)  # termo normalizado -> id
    categorias_por_nome: dict = field(default_factory=dict)  # nome/slug normalizado -> id
    regras: list = field(default_factory=list)               # [(categoria_id, [termos], peso)]
    pontuacao_minima: int = 2

    def __post_init__(self):
        self._regras = [
            (categoria_id, [_padrao(t) for t in termos if t], max(int(peso or 1), 1))
            for categoria_id, termos, peso in self.regras
        ]

    @classmethod
    def montar(cls, *, categoria_padrao, mapeamentos=(), categorias=(), regras=(),
               pontuacao_minima=2):
        """Monta a partir de tuplas vindas do banco.

        mapeamentos: [(e_da_fonte: bool, termo, categoria_id)]
        categorias:  [(categoria_id, nome, slug)]
        regras:      [(categoria_id, "palavras, separadas", peso)]
        """
        da_fonte, globais, por_nome = {}, {}, {}
        for e_da_fonte, termo, categoria_id in mapeamentos:
            chave = normalizar_texto(termo)
            if chave:
                (da_fonte if e_da_fonte else globais)[chave] = categoria_id
        for categoria_id, nome, slug in categorias:
            for chave in (normalizar_texto(nome), normalizar_texto((slug or "").replace("-", " "))):
                if chave:
                    por_nome.setdefault(chave, categoria_id)
        return cls(
            categoria_padrao=categoria_padrao,
            mapeamentos_fonte=da_fonte,
            mapeamentos_globais=globais,
            categorias_por_nome=por_nome,
            regras=[(cid, separar_termos(palavras), peso) for cid, palavras, peso in regras],
            pontuacao_minima=pontuacao_minima,
        )

    def pontuar(self, titulo, resumo):
        titulo = normalizar_texto(titulo)
        resumo = normalizar_texto(resumo)
        pontos = {}
        for categoria_id, padroes, peso in self._regras:
            total = 0
            for padrao in padroes:
                total += len(padrao.findall(titulo)) * PESO_TITULO * peso
                total += len(padrao.findall(resumo)) * PESO_RESUMO * peso
            if total:
                pontos[categoria_id] = pontos.get(categoria_id, 0) + total
        return pontos

    def categorizar(self, titulo, resumo="", termos_origem=()):
        """Devolve (categoria_id, motivo)."""
        termos = [normalizar_texto(t) for t in termos_origem or () if t]
        for termo in termos:
            if termo in self.mapeamentos_fonte:
                return self.mapeamentos_fonte[termo], "mapeamento_fonte"
        for termo in termos:
            if termo in self.mapeamentos_globais:
                return self.mapeamentos_globais[termo], "mapeamento_global"
        for termo in termos:
            if termo in self.categorias_por_nome:
                return self.categorias_por_nome[termo], "nome_categoria"
        pontos = self.pontuar(titulo, resumo)
        if pontos:
            melhor = max(pontos.items(), key=lambda par: par[1])
            if melhor[1] >= self.pontuacao_minima:
                return melhor[0], "palavras_chave"
        return self.categoria_padrao, "padrao"
