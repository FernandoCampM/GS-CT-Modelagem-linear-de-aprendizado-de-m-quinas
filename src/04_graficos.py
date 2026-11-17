# -*- coding: utf-8 -*-
"""
=============================================================================
Disciplina : Modelagem Linear e Aprendizado de Máquina — Ciência da Computação (1º semestre) — FIAP
Trabalho   : Global Solution CitizenTech — Enchentes e alagamentos em São Paulo
Integrantes:
    Fernando Campos Garnica Mota  — RM 567451
    André da Silva Pinto          — RM 559038
-----------------------------------------------------------------------------
Script 04 — Gráficos (Exercício 03)
    Figura 1: HISTOGRAMA de chuva_dia_mm (dias chuvosos), com as mesmas classes
              de Sturges da tabela contínua e linhas de média, mediana e P95.
    Figura 2: BARRAS da precipitação total por mês (jan/2025 a out/2026),
              destacando os meses com dias descartados e o último mês da série.
    Figura 3 (extra): BOXPLOT de pico_mm_h por mês do calendário.
    Todos com título, rótulos de eixos com unidade, cores definidas, legenda,
    grade leve e nota de fonte. PNG a 300 dpi em saidas/graficos/.
=============================================================================
"""
import matplotlib

matplotlib.use("Agg")  # gera arquivos sem abrir janela
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

from comum import ARQ_DIARIA, NOTA_FONTE, PASTA_GRAFICOS, carregar_resultados, salvar_secao

# Paleta (cores fixas, validadas para daltonismo na ordem azul → laranja → verde-água).
AZUL = "#2a78d6"
LARANJA = "#eb6834"
VERDE_AGUA = "#1baf7a"
AZUL_CLARO = "#a9c9ef"
TEXTO = "#0b0b0b"
TEXTO_2 = "#52514e"
GRADE = "#d9d8d4"
MESES_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
DPI = 300

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 13,
    "axes.titleweight": "bold", "axes.labelsize": 10.5, "axes.edgecolor": TEXTO_2,
    "axes.labelcolor": TEXTO, "xtick.color": TEXTO_2, "ytick.color": TEXTO_2,
    "axes.spines.top": False, "axes.spines.right": False,
})


def num_br(valor: float, casas: int = 2) -> str:
    """Formata número com vírgula decimal (padrão brasileiro)."""
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def finalizar(fig, ax, nome_arquivo: str, nota_extra: str = "") -> str:
    ax.grid(axis="y", color=GRADE, linewidth=0.6)
    ax.set_axisbelow(True)
    nota = NOTA_FONTE + (". " + nota_extra if nota_extra else "")
    fig.text(0.01, 0.01, nota, fontsize=8, color=TEXTO_2, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.02 + 0.025 * (nota.count("\n") + 1), 1, 1))
    caminho = PASTA_GRAFICOS / nome_arquivo
    fig.savefig(caminho, dpi=DPI, facecolor="white")
    plt.close(fig)
    return caminho.name


def histograma(chuvosos: pd.DataFrame, sturges: dict) -> tuple[str, dict]:
    serie = chuvosos["chuva_dia_mm"]
    media, mediana = serie.mean(), serie.median()
    p95 = serie.quantile(0.95)  # mesmo método (linear) usado no script 05
    limites = sturges["limites"]

    fig, ax = plt.subplots(figsize=(10, 5.6))
    fi, _, _ = ax.hist(serie, bins=limites, color=AZUL, edgecolor="white", linewidth=1.5,
                       label=f"Dias chuvosos (n = {len(serie)})")
    # Rótulo de frequência em cima de cada barra (ajuda a ver as classes pequenas).
    for li, ls, f in zip(limites[:-1], limites[1:], fi):
        ax.text((li + ls) / 2, f + 1.5, f"{int(f)}", ha="center", va="bottom", fontsize=8.5, color=TEXTO)

    linhas = [(media, LARANJA, "--", f"Média = {num_br(media)} mm"),
              (mediana, VERDE_AGUA, "-", f"Mediana = {num_br(mediana)} mm"),
              (p95, TEXTO, ":", f"P95 = {num_br(p95)} mm")]
    for valor, cor, estilo, rotulo in linhas:
        ax.axvline(valor, color=cor, linestyle=estilo, linewidth=2, label=rotulo)

    ax.set_xticks(limites)
    ax.set_xticklabels([num_br(v, 1) for v in limites], rotation=0, fontsize=8.5)
    ax.set_xlim(limites[0], limites[-1])
    ax.set_ylim(0, max(fi) * 1.12)
    ax.set_title("Distribuição da precipitação diária nos dias chuvosos\n"
                 "Estação A701 (São Paulo - Mirante), jan/2025 a out/2026", loc="left")
    ax.set_xlabel("Precipitação diária (mm) — classes de Sturges [li ; ls), h = "
                  f"{num_br(sturges['h'], 1)} mm")
    ax.set_ylabel("Frequência absoluta (nº de dias)")
    ax.legend(frameon=False, loc="upper right")
    nome = finalizar(fig, ax, "fig1_histograma_chuva_diaria.png",
                     "Dia chuvoso: precipitação ≥ 1,0 mm")
    return nome, {"media": media, "mediana": mediana, "p95": p95}


def barras_mensais(diaria: pd.DataFrame, dias_descartados: list) -> tuple[str, list]:
    validos = diaria[diaria["dia_valido"]]
    total = validos.groupby(["ano", "mes"])["chuva_dia_mm"].sum()
    descartes = pd.Series([pd.Timestamp(d["data"]) for d in dias_descartados], dtype="datetime64[ns]")
    n_desc = descartes.groupby([descartes.dt.year, descartes.dt.month]).size() if len(descartes) else pd.Series()

    meses = pd.period_range(diaria["data"].min(), diaria["data"].max(), freq="M")
    ultimo = meses[-1]
    registros = []
    for p in meses:
        registros.append({
            "ano": p.year, "mes": p.month, "rotulo": f"{MESES_PT[p.month - 1]}/{str(p.year)[2:]}",
            "chuva_total_mm": round(float(total.get((p.year, p.month), 0.0)), 2),
            "dias_descartados": int(n_desc.get((p.year, p.month), 0)),
            "ultimo_mes_da_serie": p == ultimo,
        })
    tab = pd.DataFrame(registros)

    # Tamanho próximo ao que a figura ocupa no PDF (17 cm ≈ 6,7 pol), para que as fontes
    # não encolham demais quando a imagem é reduzida para caber na página.
    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    x = range(len(tab))
    completo = (tab["dias_descartados"] == 0) & (~tab["ultimo_mes_da_serie"])
    cores = [AZUL if c else AZUL_CLARO for c in completo]
    hachuras = ["" if c else "////" for c in completo]
    barras = ax.bar(x, tab["chuva_total_mm"], color=cores, edgecolor="white", linewidth=1.2, width=0.8)
    for b, h in zip(barras, hachuras):
        if h:
            b.set_hatch(h)
            b.set_edgecolor(AZUL)
            b.set_linewidth(0.6)
    for xi, r in zip(x, tab.itertuples()):
        ax.text(xi, r.chuva_total_mm + 4, num_br(r.chuva_total_mm, 0), ha="center", va="bottom",
                fontsize=8, color=TEXTO)
        if r.dias_descartados:
            ax.text(xi, r.chuva_total_mm + 24, f"−{r.dias_descartados} d", ha="center", va="bottom",
                    fontsize=8, color=TEXTO_2, weight="bold")

    # Separação visual entre os anos.
    corte = tab.index[tab["ano"] == 2026][0] - 0.5
    ax.axvline(corte, color=TEXTO_2, linewidth=0.8)
    topo = tab["chuva_total_mm"].max() * 1.22
    ax.text(corte - 0.3, topo * 0.97, "2025", ha="right", va="top", fontsize=10, color=TEXTO_2, weight="bold")
    ax.text(corte + 0.3, topo * 0.97, "2026", ha="left", va="top", fontsize=10, color=TEXTO_2, weight="bold")

    ax.set_xticks(list(x))
    ax.set_xticklabels(tab["rotulo"], rotation=45, ha="right", rotation_mode="anchor", fontsize=9)
    ax.set_ylim(0, topo)
    ax.set_xlim(-0.6, len(tab) - 0.4)
    ax.tick_params(axis="y", labelsize=9)
    ax.set_title("Precipitação total por mês\n"
                 "Estação A701 (São Paulo - Mirante), jan/2025 a out/2026", loc="left")
    ax.set_xlabel("Mês/ano")
    ax.set_ylabel("Precipitação total no mês (mm)")
    legenda = [Patch(facecolor=AZUL, label="Mês com todos os dias válidos"),
               Patch(facecolor=AZUL_CLARO, edgecolor=AZUL, hatch="////",
                     label="Mês possivelmente incompleto")]
    # Legenda no alto, na região livre entre fev/25 e dez/25.
    ax.legend(handles=legenda, frameon=True, facecolor="white", edgecolor="none", framealpha=0.9,
              loc="upper left", bbox_to_anchor=(0.12, 0.88), fontsize=9)
    nome = finalizar(fig, ax, "fig2_precipitacao_mensal.png",
                     "\"−n d\" = nº de dias descartados no mês (< 20 h de dados).\n"
                     f"Último mês da série: {MESES_PT[ultimo.month - 1]}/{ultimo.year} "
                     "(último dado: 31/10/2026, 20h local)")
    return nome, tab.to_dict(orient="records")


def boxplot_pico(chuvosos: pd.DataFrame) -> str:
    grupos = [chuvosos.loc[chuvosos["mes"] == m, "pico_mm_h"].values for m in range(1, 13)]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    bp = ax.boxplot(grupos, patch_artist=True, widths=0.6,
                    medianprops={"color": LARANJA, "linewidth": 2},
                    boxprops={"facecolor": AZUL_CLARO, "edgecolor": AZUL},
                    whiskerprops={"color": AZUL}, capprops={"color": AZUL},
                    flierprops={"marker": "o", "markersize": 4, "markerfacecolor": AZUL,
                                "markeredgecolor": "white"})
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels([f"{m}\n(n={len(g)})" for m, g in zip(MESES_PT, grupos)], fontsize=8.5)
    ax.set_title("Intensidade máxima horária nos dias chuvosos, por mês\n"
                 "Estação A701 (São Paulo - Mirante), jan/2025 a out/2026", loc="left")
    ax.set_xlabel("Mês do calendário (n = nº de dias chuvosos no mês, somando 2025 e 2026)")
    ax.set_ylabel("Pico de precipitação horária (mm/h)")
    ax.legend(handles=[Patch(facecolor=AZUL_CLARO, edgecolor=AZUL, label="Caixa: Q1 a Q3"),
                       plt.Line2D([], [], color=LARANJA, linewidth=2, label="Mediana"),
                       plt.Line2D([], [], color=AZUL, marker="o", linestyle="", markersize=4,
                                  markeredgecolor="white", label="Valores atípicos (> 1,5·AIQ)")],
              frameon=False, loc="upper right")
    return finalizar(fig, ax, "fig3_boxplot_pico_por_mes.png",
                     "Nov e dez só têm dados de 2025")


def main():
    diaria = pd.read_csv(ARQ_DIARIA, parse_dates=["data"])
    diaria["dia_valido"] = diaria["dia_valido"].astype(bool)
    chuvosos = diaria[diaria["dia_chuvoso"] == True]  # noqa: E712
    resultados = carregar_resultados()
    sturges = resultados["tabelas_frequencia"]["continua"]["sturges"]
    descartados = resultados["tratamento"]["datas_descartadas"]

    PASTA_GRAFICOS.mkdir(parents=True, exist_ok=True)
    f1, linhas_hist = histograma(chuvosos, sturges)
    f2, mensal = barras_mensais(diaria, descartados)
    f3 = boxplot_pico(chuvosos)

    salvar_secao("graficos", {
        "arquivos": [f1, f2, f3],
        "histograma_linhas": {k: round(float(v), 2) for k, v in linhas_hist.items()},
        "precipitacao_mensal": mensal,
    })

    # ---- Checkpoint ----
    print("Gráficos gerados em saidas/graficos/:")
    for f in (f1, f2, f3):
        print("   ", f)
    print("\nLinhas do histograma:", {k: round(float(v), 2) for k, v in linhas_hist.items()})
    print("\nPrecipitação mensal (mm):")
    print(pd.DataFrame(mensal)[["rotulo", "chuva_total_mm", "dias_descartados"]].to_string(index=False))


if __name__ == "__main__":
    main()
