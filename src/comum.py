# -*- coding: utf-8 -*-
"""
=============================================================================
Disciplina : Estatística — Ciência da Computação (3º semestre) — FIAP
Trabalho   : Global Solution CitizenTech — Enchentes e alagamentos em São Paulo
Integrantes:
    Fernando Campos Garnica Mota  — RM 567451
    André da Silva Pinto          — RM 559038
-----------------------------------------------------------------------------
Módulo comum — constantes e funções compartilhadas pelos scripts 01 a 06
    Caminhos do projeto, lista de integrantes, fonte dos dados e leitura/
    gravação de saidas/resultados.json (fonte única de todos os números).
=============================================================================
"""
import json
import math
import sys
from pathlib import Path

import pandas as pd

# Garante que acentos e símbolos (Σ, ≥, →) apareçam no terminal do Windows sem erro.
for _fluxo in (sys.stdout, sys.stderr):
    if hasattr(_fluxo, "reconfigure"):
        _fluxo.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
PASTA_BRUTOS = RAIZ / "dados" / "brutos"
PASTA_PROCESSADOS = RAIZ / "dados" / "processados"
PASTA_SAIDAS = RAIZ / "saidas"
PASTA_TABELAS = PASTA_SAIDAS / "tabelas"
PASTA_GRAFICOS = PASTA_SAIDAS / "graficos"
PASTA_ENTREGA = RAIZ / "entrega"
ARQ_RESULTADOS = PASTA_SAIDAS / "resultados.json"
ARQ_HORARIA = PASTA_PROCESSADOS / "chuva_A701_horaria.csv"
ARQ_DIARIA = PASTA_PROCESSADOS / "chuva_A701_diaria.csv"

DISCIPLINA = "Estatística — Ciência da Computação (3º semestre) — FIAP"
TRABALHO = "Global Solution CitizenTech — Enchentes e alagamentos em São Paulo"
INTEGRANTES = [
    ("Fernando Campos Garnica Mota", "567451"),
    ("André da Silva Pinto", "559038"),
]
FONTE_DADOS = ("INMET — Instituto Nacional de Meteorologia, Dados Históricos Anuais, "
               "estação automática A701 (São Paulo - Mirante de Santana)")
LINKS_DADOS = [
    "https://portal.inmet.gov.br/uploads/dadoshistoricos/2025.zip",
    "https://portal.inmet.gov.br/uploads/dadoshistoricos/2026.zip",
]
NOTA_FONTE = "Fonte: INMET, estação A701, 2025–2026"


def carregar_resultados() -> dict:
    """Lê resultados.json (ou devolve dicionário vazio se ainda não existir)."""
    if ARQ_RESULTADOS.exists():
        return json.loads(ARQ_RESULTADOS.read_text(encoding="utf-8"))
    return {}


def salvar_secao(nome: str, conteudo: dict) -> None:
    """Grava/atualiza uma seção de resultados.json sem apagar as outras."""
    ARQ_RESULTADOS.parent.mkdir(parents=True, exist_ok=True)
    resultados = carregar_resultados()
    resultados[nome] = conteudo
    ARQ_RESULTADOS.write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Distribuição de frequências (usadas nos scripts 03 e 05)
# ---------------------------------------------------------------------------
def completar_frequencias(fi: pd.Series) -> pd.DataFrame:
    """A partir de fi, calcula fri, fri%, Fi (acumulada), Fri e Fri%."""
    n = fi.sum()
    tabela = pd.DataFrame({"fi": fi.astype(int)})
    tabela["fri"] = tabela["fi"] / n
    tabela["fri_%"] = tabela["fri"] * 100
    tabela["Fi"] = tabela["fi"].cumsum()
    tabela["Fri"] = tabela["Fi"] / n
    tabela["Fri_%"] = tabela["Fri"] * 100
    return tabela



def parametros_sturges(serie: pd.Series) -> dict:
    """
    Regra de Sturges: k = 1 + 3,322·log10(n), arredondado para o inteiro mais
    próximo. É a regra clássica dos livros de estatística básica e dá um número
    de classes adequado para n na casa das centenas.
    Amplitude total AT = máx − mín; amplitude de classe h = AT / k arredondada
    PARA CIMA na precisão do dado (0,1 mm), para que as k classes cubram o máximo.
    """
    n = int(serie.count())
    k_bruto = 1 + 3.322 * math.log10(n)
    k = int(round(k_bruto))
    minimo, maximo = float(serie.min()), float(serie.max())
    at = round(maximo - minimo, 1)
    h = math.ceil(at / k * 10) / 10
    # Classes fechadas à esquerda: se k·h coincidir com AT o máximo cairia fora
    # da última classe [li, ls); nesse caso h cresce mais 0,1 mm.
    if round(minimo + k * h, 1) <= maximo:
        h = round(h + 0.1, 1)
    limites = [round(minimo + i * h, 1) for i in range(k + 1)]
    return {"n": n, "k_bruto": round(k_bruto, 4), "k": k, "minimo": minimo, "maximo": maximo,
            "amplitude_total": at, "h_bruto": round(at / k, 4), "h": h, "limites": limites}


def tabela_continua(serie: pd.Series, param: dict) -> pd.DataFrame:
    limites = param["limites"]
    classes = pd.cut(serie, bins=limites, right=False)  # [li, ls)
    fi = classes.value_counts().sort_index()
    tabela = completar_frequencias(fi)
    tabela.insert(0, "classe", [f"[{a:.1f} ; {b:.1f})" for a, b in zip(limites[:-1], limites[1:])])
    tabela.insert(1, "li", limites[:-1])
    tabela.insert(2, "ls", limites[1:])
    tabela.insert(3, "xi", [round((a + b) / 2, 2) for a, b in zip(limites[:-1], limites[1:])])
    return tabela.reset_index(drop=True)
