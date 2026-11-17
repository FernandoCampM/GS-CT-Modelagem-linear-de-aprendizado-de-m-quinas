# -*- coding: utf-8 -*-
"""
=============================================================================
Disciplina : Modelagem Linear e Aprendizado de Máquina — Ciência da Computação (1º semestre) — FIAP
Trabalho   : Global Solution CitizenTech — Enchentes e alagamentos em São Paulo
Integrantes:
    Fernando Campos Garnica Mota  — RM 567451
    André da Silva Pinto          — RM 559038
-----------------------------------------------------------------------------
Script 03 — Tabelas de Distribuição de Frequências (Exercício 02)
    a) Variável quantitativa DISCRETA: horas_com_chuva (nº de horas do dia
       com chuva > 0), uma linha por valor observado.
    b) Variável quantitativa CONTÍNUA: chuva_dia_mm (volume diário), agrupada
       em classes pela regra de Sturges, classes [li, ls).
    Ambas usam só os DIAS CHUVOSOS (chuva_dia_mm >= 1,0 mm) — ver justificativa
    abaixo. Salva CSVs em saidas/tabelas/ e os parâmetros em resultados.json.
=============================================================================
"""
import numpy as np
import pandas as pd

from comum import (ARQ_DIARIA, PASTA_TABELAS, completar_frequencias, parametros_sturges,
                   salvar_secao, tabela_continua)

# Por que só dias chuvosos? Cerca de 69% dos dias válidos são secos. Com eles,
# a tabela teria um único valor (0 h / 0 mm) concentrando quase tudo e esconderia
# o que interessa para o app: COMO a chuva se comporta QUANDO chove.
CASAS = 4  # casas decimais das frequências relativas nos CSVs


def tabela_discreta(serie: pd.Series) -> pd.DataFrame:
    """Variável discreta: cada valor observado é uma linha (não há classes)."""
    fi = serie.value_counts().sort_index()
    tabela = completar_frequencias(fi)
    tabela.index.name = "horas_com_chuva"
    return tabela.reset_index()


def conferir(tabela: pd.DataFrame, n: int, nome: str) -> dict:
    soma_fi = int(tabela["fi"].sum())
    soma_fri = float(tabela["fri"].sum())
    assert soma_fi == n, f"{nome}: Σfi = {soma_fi} ≠ n = {n}"
    assert np.isclose(soma_fri, 1.0), f"{nome}: Σfri = {soma_fri} ≠ 1"
    return {"soma_fi": soma_fi, "soma_fri": round(soma_fri, 10)}


def formatar_terminal(tabela: pd.DataFrame) -> str:
    t = tabela.copy()
    for c in ["fri", "Fri"]:
        t[c] = t[c].map(lambda v: f"{v:.4f}")
    for c in ["fri_%", "Fri_%"]:
        t[c] = t[c].map(lambda v: f"{v:.2f}")
    return t.to_string(index=False)


def main():
    diaria = pd.read_csv(ARQ_DIARIA, parse_dates=["data"])
    chuvosos = diaria[diaria["dia_chuvoso"] == True]  # noqa: E712
    n = len(chuvosos)

    # a) Discreta
    disc = tabela_discreta(chuvosos["horas_com_chuva"].astype(int))
    conf_disc = conferir(disc, n, "discreta")

    # b) Contínua
    param = parametros_sturges(chuvosos["chuva_dia_mm"])
    cont = tabela_continua(chuvosos["chuva_dia_mm"], param)
    conf_cont = conferir(cont, n, "contínua")

    PASTA_TABELAS.mkdir(parents=True, exist_ok=True)
    disc.round(CASAS).to_csv(PASTA_TABELAS / "tabela_freq_discreta_horas_com_chuva.csv", index=False)
    cont.round(CASAS).to_csv(PASTA_TABELAS / "tabela_freq_continua_chuva_dia_mm.csv", index=False)

    salvar_secao("tabelas_frequencia", {
        "populacao": "dias chuvosos (chuva_dia_mm >= 1,0 mm), dias válidos",
        "n_dias_chuvosos": n,
        "discreta": {
            "variavel": "horas_com_chuva", "unidade": "h", **conf_disc,
            "linhas": disc.round(6).to_dict(orient="records"),
        },
        "continua": {
            "variavel": "chuva_dia_mm", "unidade": "mm", **conf_cont,
            "sturges": param,
            "linhas": cont.round(6).to_dict(orient="records"),
        },
    })

    # ---- Checkpoint ----
    print(f"População: {n} dias chuvosos (>= 1,0 mm)\n")
    print("a) Tabela de frequências — horas_com_chuva (discreta, h)")
    print(formatar_terminal(disc))
    print(f"   Conferência: Σfi = {conf_disc['soma_fi']} | Σfri = {conf_disc['soma_fri']:.4f}\n")
    p = param
    print("b) Tabela de frequências — chuva_dia_mm (contínua, mm) — regra de Sturges")
    print(f"   k = 1 + 3,322·log10({p['n']}) = {p['k_bruto']:.4f} → k = {p['k']} classes")
    print(f"   AT = {p['maximo']:.1f} − {p['minimo']:.1f} = {p['amplitude_total']:.1f} mm")
    print(f"   h = AT/k = {p['h_bruto']:.4f} → h = {p['h']:.1f} mm (arredondado para cima)")
    print(formatar_terminal(cont.drop(columns=["li", "ls"])))
    print(f"   Conferência: Σfi = {conf_cont['soma_fi']} | Σfri = {conf_cont['soma_fri']:.4f}")


if __name__ == "__main__":
    main()
