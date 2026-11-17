# -*- coding: utf-8 -*-
"""
=============================================================================
Disciplina : Modelagem Linear e Aprendizado de Máquina — Ciência da Computação (1º semestre) — FIAP
Trabalho   : Global Solution CitizenTech — Enchentes e alagamentos em São Paulo
Integrantes:
    Fernando Campos Garnica Mota  — RM 567451
    André da Silva Pinto          — RM 559038
-----------------------------------------------------------------------------
Script 05 — Estatística descritiva (Exercício 04)
    Duas análises univariadas, nos DIAS CHUVOSOS (>= 1,0 mm):
      1) chuva_dia_mm — volume diário (mm)
      2) pico_mm_h    — intensidade máxima horária do dia (mm/h)
    Para cada uma: a) média, mediana e moda (Czuber + moda bruta);
    b) máximo, mínimo, amplitude, variância amostral, desvio padrão e CV;
    c) quartis e AIQ; extras: P90, P95, P99 (limiares de alerta).
    As medidas são calculadas por funções próprias (media, mediana, moda,
    variancia, desvio_padrao, quantil...), no estilo das aulas, e conferidas
    contra o pandas: se alguma divergir, o script para com erro.
    Calcula também os números de apoio aos insights do relatório
    (sazonalidade e hora dos picos). Tudo vai para saidas/resultados.json.
=============================================================================
"""
import math

import pandas as pd

from comum import (ARQ_DIARIA, ARQ_HORARIA, PASTA_TABELAS, parametros_sturges,
                   salvar_secao, tabela_continua)

VARIAVEIS = {
    "chuva_dia_mm": {"nome": "Volume diário de chuva", "unidade": "mm"},
    "pico_mm_h": {"nome": "Intensidade máxima horária", "unidade": "mm/h"},
}
# Classificação do CV usada (Pimentel-Gomes, 1985, Curso de Estatística Experimental):
#   CV < 10% → baixa; 10% ≤ CV < 20% → média; 20% ≤ CV < 30% → alta; CV ≥ 30% → muito alta.
# O critério nasceu na experimentação agrícola; aqui serve de referência. Com CV acima
# de 100%, qualquer convenção usual (inclusive a didática 15%/30%) leva à mesma conclusão.
LIMITES_CV = (10, 20, 30)
PERCENTIS_ALERTA = [0.90, 0.95, 0.99]
MESES_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


# =============================================================================
# Funções de estatística descritiva escritas "à mão", no estilo das aulas (CP3):
# cada uma recebe uma lista de números e aplica a fórmula diretamente.
# Elas são a fonte dos valores; o pandas é usado só para CONFERIR (ver conferir()).
# =============================================================================

def media(lista: list) -> float:
    """Média aritmética: x̄ = Σxi / n."""
    return sum(lista) / len(lista)


def mediana(lista: list) -> float:
    """Valor central da lista ordenada. Com n par, é a média dos dois centrais."""
    ordenada = sorted(lista)
    n = len(ordenada)
    meio = n // 2
    if n % 2 == 1:
        return ordenada[meio]
    return (ordenada[meio - 1] + ordenada[meio]) / 2


def moda(lista: list) -> tuple[list, int]:
    """
    Moda bruta: valor(es) que mais se repete(m). Devolve a lista de modas
    (pode haver mais de uma) e quantas vezes elas aparecem.
    """
    contagem = {}
    for valor in lista:
        contagem[valor] = contagem.get(valor, 0) + 1
    freq_max = max(contagem.values())
    modas = sorted(valor for valor, freq in contagem.items() if freq == freq_max)
    return modas, freq_max


def maximo(lista: list) -> float:
    maior = lista[0]
    for valor in lista:
        if valor > maior:
            maior = valor
    return maior


def minimo(lista: list) -> float:
    menor = lista[0]
    for valor in lista:
        if valor < menor:
            menor = valor
    return menor


def amplitude(lista: list) -> float:
    """Amplitude total: máximo − mínimo."""
    return maximo(lista) - minimo(lista)


def variancia(lista: list) -> float:
    """
    Variância AMOSTRAL: s² = Σ(xi − x̄)² / (n − 1).
    Divide por n − 1 porque os dias de 2025–2026 são uma amostra do comportamento
    da chuva em SP, e não a população inteira.
    """
    x_barra = media(lista)
    soma_quadrados = sum((x - x_barra) ** 2 for x in lista)
    return soma_quadrados / (len(lista) - 1)


def desvio_padrao(lista: list) -> float:
    """Desvio padrão amostral: s = √s²."""
    return variancia(lista) ** 0.5


def coeficiente_variacao(lista: list) -> float:
    """CV = s / x̄ × 100 (%)."""
    return desvio_padrao(lista) / media(lista) * 100


def quantil(lista: list, p: float) -> float:
    """
    Separatriz de ordem p (0 a 1), por interpolação linear entre as observações
    ordenadas: posição = (n − 1)·p, contando a partir de 0. Se a posição cair entre
    dois valores, toma-se o valor proporcional entre eles. É o método padrão do
    pandas e do QUARTIL.INC do Excel (tipo 7 de Hyndman & Fan).
    Ex.: Q1 = quantil(lista, 0.25); Q2 = quantil(lista, 0.50); Q3 = quantil(lista, 0.75).
    """
    ordenada = sorted(lista)
    posicao = (len(ordenada) - 1) * p
    abaixo = int(posicao)                      # índice do valor logo abaixo
    fracao = posicao - abaixo                  # quanto avançar até o próximo
    if abaixo + 1 >= len(ordenada):
        return ordenada[abaixo]
    return ordenada[abaixo] + fracao * (ordenada[abaixo + 1] - ordenada[abaixo])


def conferir(nome: str, valor_manual: float, valor_pandas: float) -> None:
    """Garante que a função manual dá o mesmo resultado que o pandas."""
    if not math.isclose(valor_manual, valor_pandas, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(f"{nome}: manual = {valor_manual} ≠ pandas = {valor_pandas}")


def classificar_cv(cv: float) -> str:
    if cv < LIMITES_CV[0]:
        return "baixa dispersão"
    if cv < LIMITES_CV[1]:
        return "média dispersão"
    if cv < LIMITES_CV[2]:
        return "alta dispersão"
    return "muito alta dispersão"


def moda_czuber(serie: pd.Series) -> dict:
    """
    Moda de Czuber para dados agrupados em classes (mesmas classes de Sturges
    da tabela de frequências):  Mo = li + d1 / (d1 + d2) · h,
    com d1 = f_modal − f_anterior e d2 = f_modal − f_posterior.
    Por que Czuber? Em variável contínua quase nenhum valor se repete de fato;
    a moda faz mais sentido como o ponto de maior concentração da distribuição,
    e Czuber o localiza dentro da classe modal levando em conta as vizinhas.
    """
    param = parametros_sturges(serie)
    tabela = tabela_continua(serie, param)
    i = int(tabela["fi"].idxmax())
    f_modal = tabela.loc[i, "fi"]
    f_ant = tabela.loc[i - 1, "fi"] if i > 0 else 0
    f_post = tabela.loc[i + 1, "fi"] if i < len(tabela) - 1 else 0
    d1, d2 = f_modal - f_ant, f_modal - f_post
    li, h = tabela.loc[i, "li"], param["h"]
    mo = li + d1 / (d1 + d2) * h
    return {"moda_czuber": round(float(mo), 4), "classe_modal": tabela.loc[i, "classe"],
            "li": float(li), "h": float(h), "f_modal": int(f_modal), "f_anterior": int(f_ant),
            "f_posterior": int(f_post), "d1": int(d1), "d2": int(d2), "sturges": param,
            "tabela_classes": tabela.round(6).to_dict(orient="records")}


def descrever(serie: pd.Series) -> dict:
    serie = serie.dropna()
    lista = [float(x) for x in serie]  # as funções manuais trabalham com listas
    n = len(lista)

    # a) Tendência central (funções manuais).
    x_barra = media(lista)
    md = mediana(lista)
    # Moda bruta: valor que mais se repete. O pluviômetro registra em passos de
    # 0,2 mm, por isso há repetições; serve como referência, não como moda principal.
    modas_brutas, freq_max = moda(lista)
    czuber = moda_czuber(serie)

    # b) Dispersão (funções manuais; variância e desvio AMOSTRAIS, divisor n − 1).
    maior, menor = maximo(lista), minimo(lista)
    amp = amplitude(lista)
    s2 = variancia(lista)
    s = desvio_padrao(lista)
    cv = coeficiente_variacao(lista)

    # c) Separatrizes (função manual, interpolação linear = tipo 7 de Hyndman & Fan).
    q1, q2, q3 = quantil(lista, 0.25), quantil(lista, 0.50), quantil(lista, 0.75)
    aiq = q3 - q1
    lim_sup_atipico = q3 + 1.5 * aiq
    percentis = {f"P{int(p * 100)}": quantil(lista, p) for p in PERCENTIS_ALERTA}

    # Conferência: cada função manual precisa bater com o pandas.
    conferir("média", x_barra, serie.mean())
    conferir("mediana", md, serie.median())
    contagem = serie.value_counts()
    conferir("moda (frequência)", freq_max, contagem.max())
    if modas_brutas != sorted(float(v) for v in contagem[contagem == contagem.max()].index):
        raise ValueError("moda: manual ≠ pandas")
    conferir("máximo", maior, serie.max())
    conferir("mínimo", menor, serie.min())
    conferir("variância", s2, serie.var(ddof=1))
    conferir("desvio padrão", s, serie.std(ddof=1))
    conferir("Q1", q1, serie.quantile(0.25))
    conferir("Q2", q2, serie.quantile(0.50))
    conferir("Q3", q3, serie.quantile(0.75))
    for p in PERCENTIS_ALERTA:
        conferir(f"P{int(p * 100)}", percentis[f"P{int(p * 100)}"], serie.quantile(p))

    return {
        "n": n,
        "media": x_barra, "mediana": md,
        "moda_czuber": czuber["moda_czuber"], "moda_bruta": modas_brutas,
        "moda_bruta_frequencia": freq_max,
        "detalhe_czuber": czuber,
        "maximo": maior, "minimo": menor, "amplitude": amp,
        "variancia": s2, "desvio_padrao": s,
        "cv_pct": cv, "cv_classificacao": classificar_cv(cv),
        "Q1": q1, "Q2": q2, "Q3": q3, "AIQ": aiq,
        "limite_superior_atipicos": lim_sup_atipico,
        "n_atipicos_acima": int((serie > lim_sup_atipico).sum()),
        "assimetria": float(serie.skew()),
        **percentis,
        "n_acima_Q3": int((serie > q3).sum()),
        "n_acima_P90": int((serie > percentis["P90"]).sum()),
        "n_acima_P95": int((serie > percentis["P95"]).sum()),
        "n_acima_P99": int((serie > percentis["P99"]).sum()),
    }


def numeros_para_insights(diaria: pd.DataFrame, chuvosos: pd.DataFrame, med: dict) -> dict:
    """Contagens usadas na seção de insights (sazonalidade, hora do pico etc.)."""
    validos = diaria[diaria["dia_valido"]]
    p90_pico, p95_pico = med["pico_mm_h"]["P90"], med["pico_mm_h"]["P95"]
    p95_chuva = med["chuva_dia_mm"]["P95"]

    # Por mês do calendário (somando 2025 e 2026).
    por_mes = []
    for m in range(1, 13):
        v = validos[validos["mes"] == m]
        c = chuvosos[chuvosos["mes"] == m]
        anos = sorted(int(a) for a in v["ano"].unique())
        por_mes.append({
            "mes": m, "mes_nome": MESES_PT[m - 1], "anos_com_dados": anos,
            "dias_validos": int(len(v)), "dias_chuvosos": int(len(c)),
            "pct_dias_chuvosos": round(100 * len(c) / len(v), 2) if len(v) else None,
            "chuva_total_mm": round(float(v["chuva_dia_mm"].sum()), 2),
            "chuva_media_por_ano_mm": round(float(v["chuva_dia_mm"].sum()) / len(anos), 2) if anos else None,
            "dias_pico_acima_P90": int((c["pico_mm_h"] > p90_pico).sum()),
            "dias_pico_acima_P95": int((c["pico_mm_h"] > p95_pico).sum()),
            "pico_max_mm_h": float(c["pico_mm_h"].max()) if len(c) else None,
        })
    tab_mes = pd.DataFrame(por_mes)

    # Verão chuvoso (dez a mar): parcela dos dias de pico intenso.
    verao = tab_mes[tab_mes["mes"].isin([12, 1, 2, 3])]
    total_p90 = int(tab_mes["dias_pico_acima_P90"].sum())

    # Hora local em que ocorreu o pico, nos dias com pico acima do P90.
    horaria = pd.read_csv(ARQ_HORARIA, parse_dates=["datetime_local"])
    horaria["data"] = pd.to_datetime(horaria["data"])
    dias_intensos = chuvosos.loc[chuvosos["pico_mm_h"] > p90_pico, ["data", "pico_mm_h"]]
    horas_pico = []
    for r in dias_intensos.itertuples():
        h = horaria[horaria["data"] == r.data]
        horas_pico.append(int(h.loc[h["precipitacao_mm"].idxmax(), "hora"]))
    horas_pico = pd.Series(horas_pico, dtype=int)
    tarde_noite = int(horas_pico.between(14, 21).sum())  # medições das 14h às 21h locais

    # Intensidade x volume: dias com pico acima do P95 que NÃO passariam no P95 do volume diário.
    intensos = chuvosos[chuvosos["pico_mm_h"] > p95_pico]
    nao_detectados_pelo_volume = intensos[intensos["chuva_dia_mm"] <= p95_chuva]

    # Fração do total do dia que caiu na hora de pico.
    fracao_pico = (chuvosos["pico_mm_h"] / chuvosos["chuva_dia_mm"] * 100)

    return {
        "por_mes": por_mes,
        "verao_dez_mar": {
            "dias_chuvosos": int(verao["dias_chuvosos"].sum()),
            "pct_dos_dias_chuvosos": round(100 * verao["dias_chuvosos"].sum() / len(chuvosos), 2),
            "dias_pico_acima_P90": int(verao["dias_pico_acima_P90"].sum()),
            "total_dias_pico_acima_P90": total_p90,
            "pct_dos_dias_pico_acima_P90": round(100 * verao["dias_pico_acima_P90"].sum() / total_p90, 2),
            "chuva_mm": round(float(verao["chuva_total_mm"].sum()), 2),
            "pct_da_chuva_total": round(100 * verao["chuva_total_mm"].sum() / validos["chuva_dia_mm"].sum(), 2),
        },
        "hora_do_pico_dias_acima_P90": {
            "n_dias": int(len(horas_pico)),
            "contagem_por_hora": {str(k): int(v) for k, v in horas_pico.value_counts().sort_index().items()},
            "n_entre_14h_e_21h": tarde_noite,
            "pct_entre_14h_e_21h": round(100 * tarde_noite / len(horas_pico), 2),
        },
        "intensidade_vs_volume": {
            "dias_pico_acima_P95": int(len(intensos)),
            "destes_com_volume_ate_P95_diario": int(len(nao_detectados_pelo_volume)),
            "datas": [
                {"data": str(r.data.date()), "pico_mm_h": float(r.pico_mm_h), "chuva_dia_mm": float(r.chuva_dia_mm)}
                for r in intensos.sort_values("pico_mm_h", ascending=False).itertuples()
            ],
        },
        "fracao_do_dia_na_hora_de_pico_pct": {
            "mediana": round(float(fracao_pico.median()), 2),
            "media": round(float(fracao_pico.mean()), 2),
        },
    }


def main():
    diaria = pd.read_csv(ARQ_DIARIA, parse_dates=["data"])
    diaria["dia_valido"] = diaria["dia_valido"].astype(bool)
    chuvosos = diaria[diaria["dia_chuvoso"] == True].copy()  # noqa: E712

    medidas = {var: descrever(chuvosos[var]) for var in VARIAVEIS}
    insights = numeros_para_insights(diaria, chuvosos, medidas)

    # Tabela de classes do pico (usada na moda de Czuber) — salva para conferência.
    pd.DataFrame(medidas["pico_mm_h"]["detalhe_czuber"]["tabela_classes"]).to_csv(
        PASTA_TABELAS / "tabela_classes_pico_mm_h.csv", index=False)

    salvar_secao("estatistica_descritiva", {
        "populacao": "dias chuvosos (chuva_dia_mm >= 1,0 mm), dias válidos",
        "variaveis": VARIAVEIS,
        "metodo_quantil": "pandas Series.quantile, interpolação linear (Hyndman & Fan tipo 7)",
        "variancia": "amostral (ddof = 1, divisor n − 1)",
        "criterio_cv": {"fonte": "PIMENTEL-GOMES, F. Curso de estatística experimental. Piracicaba: Nobel, 1985.",
                        "baixa": "CV < 10%", "media": "10% <= CV < 20%", "alta": "20% <= CV < 30%",
                        "muito_alta": "CV >= 30%"},
        "medidas": medidas,
    })
    salvar_secao("insights", insights)

    # ---- Checkpoint ----
    linhas = [
        ("n (dias chuvosos)", "n", 0), ("Média", "media", 2), ("Mediana", "mediana", 2),
        ("Moda (Czuber)", "moda_czuber", 2), ("Máximo", "maximo", 2), ("Mínimo", "minimo", 2),
        ("Amplitude", "amplitude", 2), ("Variância (s²)", "variancia", 2),
        ("Desvio padrão (s)", "desvio_padrao", 2), ("CV (%)", "cv_pct", 2), ("Q1", "Q1", 2),
        ("Q2", "Q2", 2), ("Q3", "Q3", 2), ("AIQ", "AIQ", 2), ("P90", "P90", 2), ("P95", "P95", 2),
        ("P99", "P99", 2), ("Assimetria", "assimetria", 2), ("Atípicos (> Q3+1,5·AIQ)", "n_atipicos_acima", 0),
    ]
    tab = pd.DataFrame({
        "Medida": [l[0] for l in linhas],
        **{f"{var} ({info['unidade']})": [f"{medidas[var][l[1]]:.{l[2]}f}" for l in linhas]
           for var, info in VARIAVEIS.items()},
    })
    print(tab.to_string(index=False))
    for var in VARIAVEIS:
        m = medidas[var]
        cz = m["detalhe_czuber"]
        print(f"\n{var}: CV → {m['cv_classificacao']} | moda bruta = {m['moda_bruta']} "
              f"({m['moda_bruta_frequencia']} dias) | classe modal {cz['classe_modal']}, "
              f"d1 = {cz['d1']}, d2 = {cz['d2']}, h = {cz['h']}")
    v = insights["verao_dez_mar"]
    hp = insights["hora_do_pico_dias_acima_P90"]
    iv = insights["intensidade_vs_volume"]
    print(f"\nVerão (dez–mar): {v['pct_dos_dias_chuvosos']}% dos dias chuvosos, "
          f"{v['pct_da_chuva_total']}% da chuva, {v['dias_pico_acima_P90']}/{v['total_dias_pico_acima_P90']} dias de pico > P90")
    print(f"Hora do pico (dias > P90): {hp['pct_entre_14h_e_21h']}% entre 14h e 21h — {hp['contagem_por_hora']}")
    print(f"Dias com pico > P95: {iv['dias_pico_acima_P95']}; destes, {iv['destes_com_volume_ate_P95_diario']} "
          f"NÃO passariam do P95 do volume diário")
    print(f"Fração do total do dia na hora de pico: mediana {insights['fracao_do_dia_na_hora_de_pico_pct']['mediana']}%")


if __name__ == "__main__":
    main()
