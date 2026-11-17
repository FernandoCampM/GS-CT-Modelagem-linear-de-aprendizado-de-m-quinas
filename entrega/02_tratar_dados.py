# -*- coding: utf-8 -*-
"""
=============================================================================
Disciplina : Modelagem Linear e Aprendizado de Máquina — Ciência da Computação (1º semestre) — FIAP
Trabalho   : Global Solution CitizenTech — Enchentes e alagamentos em São Paulo
Integrantes:
    Fernando Campos Garnica Mota  — RM 567451
    André da Silva Pinto          — RM 559038
-----------------------------------------------------------------------------
Script 02 — Tratamento dos dados
    Lê os CSVs brutos da estação A701 (2025 e 2026), padroniza tipos e
    faltantes, converte o horário de UTC para Brasília (UTC-3), monta a base
    horária e a base diária, aplica a regra de qualidade (>= 20 h válidas)
    e gera o arquivo de entrega entrega/base_chuvas_A701_2025_2026.xlsx.
=============================================================================
"""
import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from comum import (ARQ_DIARIA, ARQ_HORARIA, DISCIPLINA, FONTE_DADOS, INTEGRANTES,
                   LINKS_DADOS, PASTA_BRUTOS, PASTA_ENTREGA, PASTA_PROCESSADOS,
                   TRABALHO, salvar_secao)

LINHAS_METADADOS = 8          # linhas de cabeçalho da estação antes da tabela
ENCODING_INMET = "latin-1"
MIN_HORAS_VALIDAS = 20        # regra de qualidade: dia válido com >= 20 das 24 h
LIMIAR_DIA_CHUVOSO_MM = 1.0   # critério climatológico usual de "dia de chuva"
# Horário de Brasília = UTC-3 (fixo; o Brasil não adota horário de verão desde 2019).
DESLOCAMENTO_BRASILIA = pd.Timedelta(hours=-3)
ARQ_XLSX = PASTA_ENTREGA / "base_chuvas_A701_2025_2026.xlsx"


def ler_metadados(caminho) -> dict:
    """Lê as 8 linhas iniciais (chave;valor) com os dados da estação."""
    metadados = {}
    with open(caminho, encoding=ENCODING_INMET) as arq:
        for _ in range(LINHAS_METADADOS):
            chave, valor = arq.readline().rstrip("\n").split(";")[:2]
            metadados[chave.rstrip(":").strip()] = valor.strip()
    return metadados


def normalizar_hora(serie: pd.Series) -> pd.Series:
    """Aceita os dois formatos do INMET ('0000 UTC' e '00:00') e devolve 'HH:MM'."""
    s = serie.astype(str).str.replace("UTC", "", regex=False).str.strip()
    s = s.str.replace(":", "", regex=False).str.zfill(4)
    return s.str[:2] + ":" + s.str[2:4]


def ler_csv_inmet(caminho) -> pd.DataFrame:
    """Lê um CSV do INMET, mantendo data, hora UTC e precipitação horária."""
    bruto = pd.read_csv(caminho, sep=";", decimal=",", encoding=ENCODING_INMET,
                        skiprows=LINHAS_METADADOS, dtype=str)
    bruto.columns = [c.strip() for c in bruto.columns]
    col_data = next(c for c in bruto.columns if c.upper().startswith("DATA"))
    col_hora = next(c for c in bruto.columns if c.upper().startswith("HORA"))
    col_chuva = next(c for c in bruto.columns if c.upper().startswith("PRECIPITA"))

    df = pd.DataFrame()
    data_txt = bruto[col_data].str.strip().str.replace("-", "/", regex=False)
    hora_txt = normalizar_hora(bruto[col_hora])
    df["datetime_utc"] = pd.to_datetime(data_txt + " " + hora_txt, format="%Y/%m/%d %H:%M")
    # Decimal vem com vírgula; vazios e -9999 viram NaN (dado faltante, não zero).
    chuva = pd.to_numeric(bruto[col_chuva].str.replace(",", ".", regex=False), errors="coerce")
    df["precipitacao_mm"] = chuva.where(chuva != -9999)
    return df


def montar_base_horaria(arquivos) -> pd.DataFrame:
    partes = [ler_csv_inmet(a) for a in arquivos]
    horaria = pd.concat(partes, ignore_index=True)
    horaria = horaria.drop_duplicates("datetime_utc").sort_values("datetime_utc")
    # Garante a grade horária completa: horas ausentes do arquivo viram NaN.
    grade = pd.date_range(horaria["datetime_utc"].min(), horaria["datetime_utc"].max(), freq="h")
    horaria = horaria.set_index("datetime_utc").reindex(grade).rename_axis("datetime_utc").reset_index()

    horaria["datetime_local"] = horaria["datetime_utc"] + DESLOCAMENTO_BRASILIA
    horaria["data"] = horaria["datetime_local"].dt.date
    horaria["hora"] = horaria["datetime_local"].dt.hour
    return horaria[["datetime_local", "data", "hora", "precipitacao_mm", "datetime_utc"]]


def montar_base_diaria(horaria: pd.DataFrame, inicio, fim) -> tuple[pd.DataFrame, dict]:
    grupos = horaria.groupby("data")["precipitacao_mm"]
    diaria = pd.DataFrame({
        "chuva_dia_mm": grupos.sum(min_count=1),
        "horas_com_chuva": grupos.apply(lambda s: int((s > 0).sum())),
        "pico_mm_h": grupos.max(),
        "horas_validas": grupos.count(),
    })
    diaria.index = pd.to_datetime(diaria.index)
    diaria = diaria.rename_axis("data").reset_index()

    # A conversão UTC→local cria um "pedaço" de dia antes de 01/01/2025 (3 h de
    # 31/12/2024). Ele está fora do período de estudo e é removido à parte.
    fora_periodo = diaria[(diaria["data"] < inicio) | (diaria["data"] > fim)]
    diaria = diaria[(diaria["data"] >= inicio) & (diaria["data"] <= fim)].copy()

    diaria["dia_valido"] = diaria["horas_validas"] >= MIN_HORAS_VALIDAS
    # Dia inválido: as medidas de chuva ficam vazias para não entrarem na análise
    # com valor subestimado (somar poucas horas daria um total artificialmente baixo).
    for col in ["chuva_dia_mm", "horas_com_chuva", "pico_mm_h"]:
        diaria[col] = diaria[col].where(diaria["dia_valido"])
    diaria["horas_com_chuva"] = diaria["horas_com_chuva"].astype("Int64")
    diaria["chuva_dia_mm"] = diaria["chuva_dia_mm"].round(1)
    diaria["pico_mm_h"] = diaria["pico_mm_h"].round(1)
    diaria["mes"] = diaria["data"].dt.month
    diaria["ano"] = diaria["data"].dt.year
    diaria["dia_chuvoso"] = (diaria["chuva_dia_mm"] >= LIMIAR_DIA_CHUVOSO_MM).astype("boolean")
    diaria.loc[~diaria["dia_valido"], "dia_chuvoso"] = pd.NA

    info_fora = [{"data": str(r.data.date()), "horas": int(r.horas_validas)}
                 for r in fora_periodo.itertuples()]
    return diaria, {"fragmentos_fora_do_periodo": info_fora}


def ajustar_planilha(ws, larguras=None):
    """Cabeçalho em negrito com fundo, congelamento da 1ª linha e larguras."""
    for cel in ws[1]:
        cel.font = Font(bold=True, color="FFFFFF")
        cel.fill = PatternFill("solid", fgColor="1F4E79")
        cel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"
    for i, col in enumerate(ws.iter_cols(min_row=1, max_row=min(ws.max_row, 200)), start=1):
        largura = (larguras or {}).get(i)
        if largura is None:
            largura = min(60, max(len(str(c.value)) if c.value is not None else 0 for c in col) + 2)
        ws.column_dimensions[get_column_letter(i)].width = largura


def gerar_xlsx(diaria, horaria, metadados, periodo):
    integrantes = pd.DataFrame(
        [["Disciplina", DISCIPLINA], ["Trabalho", TRABALHO]]
        + [[f"Integrante {i}", f"{nome} — RM {rm}"] for i, (nome, rm) in enumerate(INTEGRANTES, 1)]
        + [["Fonte dos dados", FONTE_DADOS]]
        + [[f"Link {i}", link] for i, link in enumerate(LINKS_DADOS, 1)]
        + [["Estação", f"{metadados['ESTACAO']} ({metadados['CODIGO (WMO)']})"],
           ["Latitude / Longitude", f"{metadados['LATITUDE']} / {metadados['LONGITUDE']}"],
           ["Altitude (m)", metadados["ALTITUDE"]],
           ["Período", f"{periodo[0]} a {periodo[1]} (horário de Brasília, UTC-3)"],
           ["Observação", "2026 é parcial: último dado publicado pelo INMET em " + periodo[1]]],
        columns=["Campo", "Valor"],
    )
    dicionario = pd.DataFrame([
        ["diaria", "data", "Dia (horário de Brasília)", "data", "—"],
        ["diaria", "chuva_dia_mm", "Precipitação total do dia (soma das horas)", "mm", "quantitativa contínua"],
        ["diaria", "horas_com_chuva", "Nº de horas do dia com precipitação > 0", "h", "quantitativa discreta (0 a 24)"],
        ["diaria", "pico_mm_h", "Maior precipitação horária do dia (intensidade)", "mm/h", "quantitativa contínua"],
        ["diaria", "horas_validas", "Nº de horas do dia com dado (não faltante)", "h", "quantitativa discreta (0 a 24)"],
        ["diaria", "dia_valido", f"Verdadeiro se horas_validas >= {MIN_HORAS_VALIDAS}; se falso, as medidas de chuva ficam vazias", "—", "qualitativa (lógica)"],
        ["diaria", "mes", "Mês (1 a 12)", "—", "qualitativa ordinal"],
        ["diaria", "ano", "Ano", "—", "qualitativa ordinal"],
        ["diaria", "dia_chuvoso", f"Verdadeiro se chuva_dia_mm >= {LIMIAR_DIA_CHUVOSO_MM:.1f} mm (critério climatológico)", "—", "qualitativa (lógica)"],
        ["horaria", "datetime_local", "Data e hora no horário de Brasília (UTC-3)", "data/hora", "—"],
        ["horaria", "data", "Dia (horário de Brasília)", "data", "—"],
        ["horaria", "hora", "Hora local (0 a 23); a medição vale para a hora que termina neste horário", "h", "—"],
        ["horaria", "precipitacao_mm", "Precipitação total na hora; vazio = dado faltante", "mm", "quantitativa contínua"],
        ["horaria", "datetime_utc", "Data e hora original do INMET (UTC)", "data/hora", "—"],
    ], columns=["aba", "coluna", "descricao", "unidade", "tipo"])

    horaria_xlsx = horaria.copy()
    horaria_xlsx["data"] = pd.to_datetime(horaria_xlsx["data"])
    PASTA_ENTREGA.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(ARQ_XLSX, engine="openpyxl") as escritor:
        integrantes.to_excel(escritor, sheet_name="integrantes", index=False)
        dicionario.to_excel(escritor, sheet_name="dicionario", index=False)
        diaria.to_excel(escritor, sheet_name="diaria", index=False)
        horaria_xlsx.to_excel(escritor, sheet_name="horaria", index=False)
        livro = escritor.book
        ajustar_planilha(livro["integrantes"], {1: 24, 2: 90})
        ajustar_planilha(livro["dicionario"], {1: 10, 2: 18, 3: 80, 4: 11, 5: 30})
        ajustar_planilha(livro["diaria"], {1: 12})
        ajustar_planilha(livro["horaria"], {1: 18, 2: 12, 5: 18})
        for linha in livro["diaria"].iter_rows(min_row=2, min_col=1, max_col=1):
            linha[0].number_format = "dd/mm/yyyy"
        for linha in livro["horaria"].iter_rows(min_row=2, max_col=5):
            linha[0].number_format = "dd/mm/yyyy hh:mm"
            linha[1].number_format = "dd/mm/yyyy"
            linha[4].number_format = "dd/mm/yyyy hh:mm"


def main():
    arquivos = sorted(PASTA_BRUTOS.glob("*A701*.CSV")) + sorted(PASTA_BRUTOS.glob("*A701*.csv"))
    arquivos = sorted(set(arquivos))
    if not arquivos:
        raise SystemExit("Nenhum CSV da A701 em dados/brutos/. Rode antes o 01_baixar_dados.py.")
    metadados = ler_metadados(arquivos[0])

    horaria = montar_base_horaria(arquivos)
    # Período de estudo em horário local: do 1º dia de 2025 ao último dia com dados.
    inicio = pd.Timestamp("2025-01-01")
    fim = pd.Timestamp(horaria["data"].max())
    diaria, info_fora = montar_base_diaria(horaria, inicio, fim)
    horaria_periodo = horaria[(pd.to_datetime(horaria["data"]) >= inicio)].reset_index(drop=True)

    PASTA_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    horaria_periodo.to_csv(ARQ_HORARIA, index=False, encoding="utf-8")
    diaria.to_csv(ARQ_DIARIA, index=False, encoding="utf-8", date_format="%Y-%m-%d")

    validos = diaria[diaria["dia_valido"]]
    descartados = diaria[~diaria["dia_valido"]]
    chuvosos = validos[validos["dia_chuvoso"] == True]  # noqa: E712
    periodo = (inicio.strftime("%d/%m/%Y"), fim.strftime("%d/%m/%Y"))
    ultimo_utc = horaria["datetime_utc"].max()

    top5 = validos.nlargest(5, "chuva_dia_mm")[["data", "chuva_dia_mm", "pico_mm_h", "horas_com_chuva"]]
    resumo = {
        "metadados_estacao": metadados,
        "arquivos_brutos": [a.name for a in arquivos],
        "periodo_inicio": str(inicio.date()),
        "periodo_fim": str(fim.date()),
        "ultimo_registro_utc": str(ultimo_utc),
        "fuso": "Horário de Brasília (UTC-3)",
        "horas_total": int(len(horaria_periodo)),
        "horas_faltantes": int(horaria_periodo["precipitacao_mm"].isna().sum()),
        "dias_total": int(len(diaria)),
        "dias_validos": int(len(validos)),
        "dias_descartados": int(len(descartados)),
        "datas_descartadas": [
            {"data": str(r.data.date()), "horas_validas": int(r.horas_validas)}
            for r in descartados.itertuples()
        ],
        **info_fora,
        "criterio_dia_valido_horas": MIN_HORAS_VALIDAS,
        "criterio_dia_chuvoso_mm": LIMIAR_DIA_CHUVOSO_MM,
        "dias_chuvosos": int(len(chuvosos)),
        "dias_secos": int(len(validos) - len(chuvosos)),
        "dias_com_alguma_chuva": int((validos["chuva_dia_mm"] > 0).sum()),
        "pct_dias_chuvosos": round(100 * len(chuvosos) / len(validos), 2),
        "chuva_total_mm": round(float(validos["chuva_dia_mm"].sum()), 2),
        "chuva_total_por_ano_mm": {
            str(a): round(float(v), 2) for a, v in validos.groupby("ano")["chuva_dia_mm"].sum().items()
        },
        "top5_chuvas_diarias": [
            {"data": str(r.data.date()), "chuva_dia_mm": float(r.chuva_dia_mm),
             "pico_mm_h": float(r.pico_mm_h), "horas_com_chuva": int(r.horas_com_chuva)}
            for r in top5.itertuples()
        ],
    }
    salvar_secao("tratamento", resumo)
    gerar_xlsx(diaria, horaria_periodo, metadados, periodo)

    # ---- Checkpoint ----
    print(f"Arquivos lidos: {', '.join(resumo['arquivos_brutos'])}")
    print(f"Período (horário local): {periodo[0]} a {periodo[1]}  | último registro UTC: {ultimo_utc}")
    print(f"Horas no período: {resumo['horas_total']}  | horas sem dado: {resumo['horas_faltantes']}")
    print(f"Dias no período: {resumo['dias_total']}  | válidos: {resumo['dias_validos']}  "
          f"| descartados (< {MIN_HORAS_VALIDAS} h): {resumo['dias_descartados']}")
    for d in resumo["datas_descartadas"]:
        print(f"    descartado: {d['data']} ({d['horas_validas']} h com dado)")
    for d in resumo["fragmentos_fora_do_periodo"]:
        print(f"    fora do período (fuso): {d['data']} ({d['horas']} h)")
    print(f"Dias chuvosos (>= {LIMIAR_DIA_CHUVOSO_MM} mm): {resumo['dias_chuvosos']} "
          f"({resumo['pct_dias_chuvosos']}% dos válidos) | dias com alguma chuva: {resumo['dias_com_alguma_chuva']}")
    print(f"Chuva total: {resumo['chuva_total_mm']} mm  | por ano: {resumo['chuva_total_por_ano_mm']}")
    print("5 maiores chuvas diárias:")
    print(top5.to_string(index=False))
    print(f"\nGerados: {ARQ_HORARIA.name}, {ARQ_DIARIA.name}, {ARQ_XLSX.name}, resultados.json")


if __name__ == "__main__":
    main()
