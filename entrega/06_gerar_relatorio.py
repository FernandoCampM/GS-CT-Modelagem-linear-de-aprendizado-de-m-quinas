# -*- coding: utf-8 -*-
"""
=============================================================================
Disciplina : Estatística — Ciência da Computação (3º semestre) — FIAP
Trabalho   : Global Solution CitizenTech — Enchentes e alagamentos em São Paulo
Integrantes:
    Fernando Campos Garnica Mota  — RM 567451
    André da Silva Pinto          — RM 559038
-----------------------------------------------------------------------------
Script 06 — Relatório estatístico em PDF (Exercício 05)
    Gera entrega/relatorio_estatistico_GS_enchentes.pdf com reportlab.
    TODOS os números vêm de saidas/resultados.json (gerado pelos scripts 02 a
    05) e as figuras de saidas/graficos/. Os poucos valores derivados (ex.:
    frequência anual de dias acima de um limiar) são calculados aqui a partir
    do JSON e gravados de volta nele, na seção "derivados_relatorio".
=============================================================================
"""
from datetime import date
from pathlib import Path

import matplotlib
from PIL import Image as ImagemPIL
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from comum import (INTEGRANTES, PASTA_ENTREGA, PASTA_GRAFICOS, carregar_resultados,
                   salvar_secao)

ARQ_PDF = PASTA_ENTREGA / "relatorio_estatistico_GS_enchentes.pdf"
AZUL_ESCURO = colors.HexColor("#1F4E79")
AZUL_CLARO = colors.HexColor("#EAF1FA")
CINZA = colors.HexColor("#52514e")
LARGURA_UTIL = A4[0] - 4 * cm
MESES_EXTENSO = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
                 "agosto", "setembro", "outubro", "novembro", "dezembro"]

# ---------------------------------------------------------------------------
# Fontes (DejaVu, que acompanha o matplotlib, tem os símbolos ≥, ², ·, −)
# ---------------------------------------------------------------------------
PASTA_FONTES = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
pdfmetrics.registerFont(TTFont("DejaVu", PASTA_FONTES / "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", PASTA_FONTES / "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Oblique", PASTA_FONTES / "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold",
                              italic="DejaVu-Oblique", boldItalic="DejaVu-Bold")

ESTILOS = {
    "corpo": ParagraphStyle("corpo", fontName="DejaVu", fontSize=9.6, leading=14.2,
                            alignment=TA_JUSTIFY, spaceAfter=6),
    "lista": ParagraphStyle("lista", fontName="DejaVu", fontSize=9.6, leading=14.2,
                            alignment=TA_JUSTIFY, leftIndent=14, bulletIndent=4, spaceAfter=3),
    "h1": ParagraphStyle("h1", fontName="DejaVu-Bold", fontSize=13.5, leading=18,
                         textColor=AZUL_ESCURO, spaceBefore=10, spaceAfter=8, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="DejaVu-Bold", fontSize=11, leading=15,
                         textColor=AZUL_ESCURO, spaceBefore=8, spaceAfter=5, keepWithNext=1),
    "legenda": ParagraphStyle("legenda", fontName="DejaVu-Bold", fontSize=8.8, leading=12,
                              alignment=TA_LEFT, spaceBefore=6, spaceAfter=3),
    "fonte": ParagraphStyle("fonte", fontName="DejaVu", fontSize=7.8, leading=10.5,
                            textColor=CINZA, spaceBefore=2, spaceAfter=10),
    "celula": ParagraphStyle("celula", fontName="DejaVu", fontSize=8.2, leading=10.5),
    "celula_c": ParagraphStyle("celula_c", fontName="DejaVu", fontSize=8.2, leading=10.5,
                               alignment=TA_CENTER),
    "cab": ParagraphStyle("cab", fontName="DejaVu-Bold", fontSize=8.2, leading=10.5,
                          textColor=colors.white, alignment=TA_CENTER),
    "ref": ParagraphStyle("ref", fontName="DejaVu", fontSize=8.8, leading=12.5,
                          alignment=TA_LEFT, spaceAfter=6, leftIndent=12, firstLineIndent=-12),
}


# ---------------------------------------------------------------------------
# Formatação de números (vírgula decimal, 2 casas, unidade)
# ---------------------------------------------------------------------------
def br(valor, casas: int = 2, unidade: str = "") -> str:
    texto = f"{float(valor):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{texto} {unidade}".strip() if unidade else texto


def data_br(iso: str) -> str:
    a, m, d = iso[:10].split("-")
    return f"{d}/{m}/{a}"


def p(texto: str, estilo: str = "corpo") -> Paragraph:
    return Paragraph(texto, ESTILOS[estilo])


def lista(itens: list[str]) -> list:
    return [Paragraph(i, ESTILOS["lista"], bulletText="•") for i in itens]


class Numeracao:
    """Numeração automática de tabelas e figuras."""
    def __init__(self):
        self.tabela = 0
        self.figura = 0

    def nova_tabela(self) -> int:
        self.tabela += 1
        return self.tabela

    def nova_figura(self) -> int:
        self.figura += 1
        return self.figura


NUM = Numeracao()


def tabela(titulo: str, cabecalho: list, linhas: list, larguras: list, fonte: str,
           alinhamentos: list | None = None, destaque_linhas: list | None = None,
           antes: list | None = None) -> KeepTogether:
    n = NUM.nova_tabela()
    alinhamentos = alinhamentos or ["c"] * len(cabecalho)
    dados = [[Paragraph(c, ESTILOS["cab"]) for c in cabecalho]]
    for linha in linhas:
        dados.append([Paragraph(str(v), ESTILOS["celula_c" if a == "c" else "celula"])
                      for v, a in zip(linha, alinhamentos)])
    t = Table(dados, colWidths=larguras, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_ESCURO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, AZUL_ESCURO),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
    ]
    for i in range(1, len(dados)):
        if i % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-1, i), AZUL_CLARO))
    for i in destaque_linhas or []:
        estilo.append(("BACKGROUND", (0, i + 1), (-1, i + 1), colors.HexColor("#FFF1D6")))
    t.setStyle(TableStyle(estilo))
    # "antes" permite manter o título da seção na mesma página da tabela.
    return KeepTogether((antes or []) + [p(f"Tabela {n} – {titulo}", "legenda"), t, p(fonte, "fonte")])


def figura(caminho: Path, titulo: str, fonte: str, largura=LARGURA_UTIL) -> KeepTogether:
    n = NUM.nova_figura()
    with ImagemPIL.open(caminho) as im:
        w, h = im.size
    img = Image(str(caminho), width=largura, height=largura * h / w)
    return KeepTogether([p(f"Figura {n} – {titulo}", "legenda"), img, p(fonte, "fonte")])


# ---------------------------------------------------------------------------
# Rodapé e capa
# ---------------------------------------------------------------------------
TEXTO_RODAPE = " · ".join(f"{nome} (RM {rm})" for nome, rm in INTEGRANTES)


def desenhar_rodape(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(AZUL_ESCURO)
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, 1.55 * cm, A4[0] - 2 * cm, 1.55 * cm)
    canvas.setFont("DejaVu", 7.2)
    canvas.setFillColor(CINZA)
    canvas.drawString(2 * cm, 1.15 * cm, TEXTO_RODAPE)
    canvas.drawString(2 * cm, 0.8 * cm, "Global Solution CitizenTech · Estatística · FIAP — Ciência da Computação")
    canvas.drawRightString(A4[0] - 2 * cm, 1.15 * cm, f"Página {doc.page}")
    canvas.restoreState()


def capa(hoje: str) -> list:
    centro = lambda tam, negrito=False, cor=colors.black, espaco=6: ParagraphStyle(  # noqa: E731
        "c", fontName="DejaVu-Bold" if negrito else "DejaVu", fontSize=tam, leading=tam * 1.35,
        alignment=TA_CENTER, textColor=cor, spaceAfter=espaco)
    integrantes = "<br/>".join(f"{nome} — RM {rm}" for nome, rm in INTEGRANTES)
    return [
        Spacer(1, 1.2 * cm),
        Paragraph("FIAP — Faculdade de Informática e Administração Paulista", centro(13, True, AZUL_ESCURO)),
        Paragraph("Bacharelado em Ciência da Computação — 3º semestre", centro(11)),
        Paragraph("Disciplina: Estatística", centro(11)),
        Spacer(1, 2.2 * cm),
        Paragraph("Global Solution: CitizenTech", centro(15, True, AZUL_ESCURO, 18)),
        Paragraph("Chuvas intensas e risco de alagamentos em São Paulo", centro(19, True, colors.black, 8)),
        Paragraph("Relatório estatístico da precipitação na estação automática INMET A701 "
                  "(São Paulo - Mirante de Santana), janeiro de 2025 a outubro de 2026",
                  centro(11.5, False, CINZA, 10)),
        Spacer(1, 3.0 * cm),
        Paragraph("Integrantes", centro(11, True)),
        Paragraph(integrantes, centro(11)),
        Spacer(1, 3.2 * cm),
        Paragraph(f"São Paulo, {hoje}", centro(11)),
        PageBreak(),
    ]


# ---------------------------------------------------------------------------
# Valores derivados (gravados no JSON para que o PDF bata com ele)
# ---------------------------------------------------------------------------
def calcular_derivados(R: dict) -> dict:
    t = R["tratamento"]
    m = R["estatistica_descritiva"]["medidas"]
    anos_equivalentes = t["dias_validos"] / 365.25
    maior = t["top5_chuvas_diarias"][0]
    derivados = {
        "anos_equivalentes_de_dados": round(anos_equivalentes, 4),
        "pct_horas_faltantes": round(100 * t["horas_faltantes"] / t["horas_total"], 2),
        "pct_dias_descartados": round(100 * t["dias_descartados"] / t["dias_total"], 2),
        "pct_dias_secos": round(100 * t["dias_secos"] / t["dias_validos"], 2),
        "maior_evento_pct_na_hora_de_pico": round(100 * maior["pico_mm_h"] / maior["chuva_dia_mm"], 2),
        "dias_por_ano_acima": {
            var: {lim: round(m[var][f"n_acima_{lim}"] / anos_equivalentes, 2)
                  for lim in ["Q3", "P90", "P95", "P99"]}
            for var in m
        },
        "pct_dias_chuvosos_acima": {
            var: {lim: round(100 * m[var][f"n_acima_{lim}"] / m[var]["n"], 2)
                  for lim in ["Q3", "P90", "P95", "P99"]}
            for var in m
        },
        "razao_media_mediana": {var: round(m[var]["media"] / m[var]["mediana"], 2) for var in m},
    }
    salvar_secao("derivados_relatorio", derivados)
    return derivados


# ---------------------------------------------------------------------------
# Conteúdo
# ---------------------------------------------------------------------------
def montar_conteudo(R: dict, D: dict) -> list:
    t = R["tratamento"]
    tf = R["tabelas_frequencia"]
    m = R["estatistica_descritiva"]["medidas"]
    V, I = m["chuva_dia_mm"], m["pico_mm_h"]
    ins = R["insights"]
    meta = t["metadados_estacao"]
    st = tf["continua"]["sturges"]
    disc = tf["discreta"]["linhas"]
    cont = tf["continua"]["linhas"]
    mensal = R["graficos"]["precipitacao_mensal"]
    verao = ins["verao_dez_mar"]
    hp = ins["hora_do_pico_dias_acima_P90"]
    ivv = ins["intensidade_vs_volume"]
    top = t["top5_chuvas_diarias"]
    maior = top[0]
    fim = data_br(t["periodo_fim"])
    n = tf["n_dias_chuvosos"]
    fonte_padrao = f"Fonte: elaborado pelos autores com dados do INMET, estação A701, 01/01/2025 a {fim}."
    por_mes = {pm["mes"]: pm for pm in ins["por_mes"]}
    linha_disc = {r["horas_com_chuva"]: r for r in disc}
    mes_max = max(mensal, key=lambda r: r["chuva_total_mm"])
    mes_min = min(mensal, key=lambda r: r["chuva_total_mm"])
    desc_txt = ", ".join(f"{data_br(d['data'])} ({d['horas_validas']} h)" for d in t["datas_descartadas"])
    c = []

    # 1. Sumário executivo -------------------------------------------------
    c += [p("1. Sumário executivo", "h1"),
          p("Alagamentos em São Paulo são provocados, em grande parte, por chuvas fortes concentradas em "
            "poucas horas, que superam a capacidade de drenagem da cidade. Este relatório analisa a "
            "precipitação horária medida pela estação automática A701 do INMET (Mirante de Santana, Zona "
            f"Norte) de 01/01/2025 a {fim}, com o objetivo de dar base estatística ao aplicativo de rotas "
            "do grupo, que pretende estimar onde e quando alagamentos são prováveis. Foram tratados "
            f"{br(t['horas_total'], 0)} registros horários, que resultaram em {t['dias_validos']} dias válidos, "
            f"dos quais {t['dias_chuvosos']} foram dias chuvosos (≥ 1,0 mm). Os principais achados são:"),
          *lista([
              f"<b>A chuva é pouco frequente e muito irregular.</b> Choveu ao menos 1,0 mm em {br(t['pct_dias_chuvosos'])}% "
              f"dos dias. Nos dias chuvosos, a média diária ({br(V['media'], 2, 'mm')}) é "
              f"{br(D['razao_media_mediana']['chuva_dia_mm'])} vez a mediana ({br(V['mediana'], 2, 'mm')}) e o "
              f"coeficiente de variação é de {br(V['cv_pct'])}%: poucos eventos extremos puxam a média para cima.",
              f"<b>Os eventos extremos são breves.</b> No maior evento da série ({data_br(maior['data'])}), "
              f"{br(maior['pico_mm_h'], 2, 'mm')} dos {br(maior['chuva_dia_mm'], 2, 'mm')} do dia "
              f"({br(D['maior_evento_pct_na_hora_de_pico'])}%) caíram em uma única hora. Na mediana dos dias "
              f"chuvosos, {br(ins['fracao_do_dia_na_hora_de_pico_pct']['mediana'])}% da chuva do dia cai na hora de pico.",
              f"<b>A intensidade horária é melhor gatilho de alerta do que o volume diário.</b> Dos "
              f"{ivv['dias_pico_acima_P95']} dias com pico acima do P95 da intensidade "
              f"({br(I['P95'], 2, 'mm/h')}), {ivv['destes_com_volume_ate_P95_diario']} não ultrapassariam o "
              f"P95 do volume diário ({br(V['P95'], 2, 'mm')}).",
              f"<b>Limiares de alerta propostos, a partir dos dados:</b> atenção acima de "
              f"{br(I['P90'], 2, 'mm/h')} (P90), alerta acima de {br(I['P95'], 2, 'mm/h')} (P95) e alerta "
              f"máximo acima de {br(I['P99'], 2, 'mm/h')} (P99) de chuva em uma hora.",
              f"<b>O risco se concentra no verão, mas não só nele.</b> De dezembro a março ocorreram "
              f"{br(verao['pct_da_chuva_total'])}% da chuva e {verao['dias_pico_acima_P90']} dos "
              f"{verao['total_dias_pico_acima_P90']} dias com pico acima do P90; janeiro lidera. Em 2026, "
              "setembro e outubro foram atipicamente chuvosos, o que reforça a necessidade de alertas o ano todo.",
          ]),
          PageBreak()]

    # 2. Contexto ----------------------------------------------------------
    c += [p("2. Contexto e problema", "h1"),
          p("A cidade de São Paulo combina alta impermeabilização do solo, rios e córregos canalizados e "
            "ocupação de antigas várzeas. Nessas condições, uma chuva intensa de curta duração produz "
            "escoamento rápido, que sobrecarrega galerias e canais e provoca alagamentos em vias, túneis "
            "e baixadas. Os efeitos atingem pedestres e motoristas, usuários de ônibus e aplicativos, "
            "comerciantes e, principalmente, moradores de áreas baixas, que podem perder bens e ficar "
            "isolados."),
          p("O grupo propõe, nas demais disciplinas da Global Solution, um aplicativo de navegação semelhante "
            "a um serviço de mapas, que usa o histórico de chuvas fortes para estimar locais com risco de "
            "alagamento e sugerir a rota menos afetada, a pé ou de carro. A hipótese central do aplicativo é "
            "que <i>chuva forte leva a alagamento</i>. Esta entrega não implementa o aplicativo: ela "
            "caracteriza estatisticamente a chuva na capital e indica <b>quais níveis de chuva</b> e "
            "<b>quais épocas do ano</b> devem disparar alertas."),
          p("O trabalho se relaciona com dois Objetivos de Desenvolvimento Sustentável da ONU: o <b>ODS 11</b> "
            "(Cidades e comunidades sustentáveis), cuja meta 11.5 trata de reduzir mortes e pessoas afetadas "
            "por desastres, inclusive os relacionados à água; e o <b>ODS 13</b> (Ação contra a mudança global do "
            "clima), cuja meta 13.1 trata de reforçar a resiliência e a capacidade de adaptação a riscos "
            "relacionados ao clima.")]

    # 3. Base de dados -----------------------------------------------------
    c += [p("3. Base de dados (Exercício 01)", "h1"),
          p("Os dados vêm dos <b>Dados Históricos Anuais</b> do Instituto Nacional de Meteorologia (INMET), "
            "que publica um arquivo por ano com os registros horários de todas as estações automáticas do país. "
            "Foram usados os arquivos de 2025 e 2026, dos quais se extraiu apenas o da estação A701. O arquivo "
            f"de 2026 é parcial: o último registro publicado é de {fim} às 23h UTC "
            "(20h no horário de Brasília)."),
          tabela("Metadados da estação A701",
                 ["Campo", "Valor"],
                 [["Estação", f"{meta['ESTACAO']} (código {meta['CODIGO (WMO)']})"],
                  ["Região / UF", f"{meta['REGIAO']} / {meta['UF']}"],
                  ["Latitude / Longitude", f"{meta['LATITUDE']} / {meta['LONGITUDE']}"],
                  ["Altitude", f"{meta['ALTITUDE']} m"],
                  ["Data de fundação", meta["DATA DE FUNDACAO"]],
                  ["Período analisado", f"01/01/2025 a {fim} (horário de Brasília)"],
                  ["Arquivos brutos", "<br/>".join(t["arquivos_brutos"])]],
                 [4.2 * cm, LARGURA_UTIL - 4.2 * cm],
                 "Fonte: INMET, Dados Históricos Anuais (metadados do cabeçalho dos arquivos CSV).",
                 ["e", "e"]),
          p("A partir da coluna <i>PRECIPITAÇÃO TOTAL, HORÁRIO (mm)</i> foram construídas as variáveis "
            "diárias da Tabela 2, que formam a base entregue em <i>base_chuvas_A701_2025_2026.xlsx</i>."),
          tabela("Variáveis da base diária",
                 ["Variável", "Descrição", "Unidade", "Tipo"],
                 [["chuva_dia_mm", "Soma da precipitação das 24 horas do dia", "mm", "Quantitativa contínua"],
                  ["horas_com_chuva", "Número de horas do dia com precipitação maior que zero", "h",
                   "Quantitativa discreta (0 a 24)"],
                  ["pico_mm_h", "Maior precipitação registrada em uma hora no dia (intensidade)", "mm/h",
                   "Quantitativa contínua"],
                  ["horas_validas", "Número de horas do dia com dado", "h", "Quantitativa discreta"],
                  ["dia_chuvoso", "Verdadeiro se chuva_dia_mm ≥ 1,0 mm", "—", "Qualitativa (lógica)"],
                  ["mes, ano", "Mês e ano do dia", "—", "Qualitativa ordinal"]],
                 [3.0 * cm, 7.2 * cm, 2.0 * cm, LARGURA_UTIL - 12.2 * cm], fonte_padrao,
                 ["e", "e", "c", "e"]),
          p("<b>Justificativa da escolha.</b> A base atende às necessidades do problema por quatro razões:"),
          *lista([
              "<b>É oficial e real:</b> o INMET é o órgão federal responsável pela meteorologia no Brasil, e os "
              "dados são medições de pluviômetro, não estimativas nem dados simulados.",
              "<b>Tem resolução horária:</b> alagamentos dependem da intensidade da chuva em poucas horas. Uma "
              "base apenas diária ou mensal esconderia exatamente o fenômeno de interesse.",
              "<b>A estação fica na capital:</b> o Mirante de Santana, na Zona Norte, é o posto meteorológico de "
              f"referência da cidade de São Paulo; a estação automática A701 opera desde {meta['DATA DE FUNDACAO']}.",
              "<b>Há ligação direta com o problema:</b> a precipitação é a variável de entrada de qualquer modelo "
              "de alagamento e é a mesma informação que o aplicativo usaria para disparar alertas.",
          ])]

    # 4. Metodologia -------------------------------------------------------
    c += [p("4. Metodologia", "h1"),
          p("4.1 Tratamento dos dados", "h2"),
          *lista([
              "Leitura dos CSVs (separador ponto e vírgula, decimal com vírgula, codificação latin-1), "
              "ignorando as 8 linhas de metadados. O código aceita os dois formatos de hora usados pelo INMET "
              "(“0000 UTC” e “00:00”).",
              f"Valores vazios ou −9999 foram tratados como <b>faltantes</b>, nunca como zero: "
              f"{t['horas_faltantes']} de {br(t['horas_total'], 0)} horas ({br(D['pct_horas_faltantes'])}%).",
              "Conversão do horário de UTC para o <b>horário de Brasília (UTC−3)</b> antes de agregar por dia, "
              "para que o “dia” corresponda ao dia vivido pela população. Como o Brasil não adota horário de "
              "verão desde 2019, o deslocamento é fixo. A conversão gera um fragmento de 3 horas em 31/12/2024, "
              "que foi removido por estar fora do período.",
              "Premissa: cada valor horário do INMET foi tratado como a chuva acumulada na hora que termina no "
              "horário indicado (o registro das 16h corresponde à chuva das 15h às 16h). Essa convenção afeta "
              "apenas a análise da hora do pico (seção 6.3), que pode estar deslocada em uma hora.",
              f"<b>Regra de qualidade:</b> um dia só é válido se tiver pelo menos {t['criterio_dia_valido_horas']} "
              f"das 24 horas com dado. Somar poucas horas subestimaria a chuva do dia. Foram descartados "
              f"{t['dias_descartados']} dos {t['dias_total']} dias ({br(D['pct_dias_descartados'])}%): {desc_txt}. "
              "O último dia, 31/10/2026, tem 21 horas (os dados terminam às 20h locais), passou na regra e "
              "não registrou chuva.",
              "<b>Dia chuvoso:</b> precipitação diária ≥ 1,0 mm, critério do índice de dias úmidos do ETCCDI "
              "(grupo de índices climáticos da Organização Meteorológica Mundial). Valores abaixo de 1,0 mm "
              "costumam ser garoa ou orvalho sem efeito sobre a drenagem.",
          ]),
          p("4.2 Decisões estatísticas", "h2"),
          *lista([
              f"<b>População analisada:</b> as tabelas e as medidas usam só os {n} dias chuvosos. Incluir os "
              f"{t['dias_secos']} dias secos ({br(D['pct_dias_secos'])}% dos válidos) colocaria quase todas as "
              "observações no valor zero e esconderia como a chuva se comporta quando ocorre.",
              "<b>Número de classes:</b> regra de Sturges, k = 1 + 3,322·log₁₀(n). A amplitude de classe h foi "
              "arredondada para cima na precisão do dado (0,1 mm), para que as classes cubram o valor máximo. "
              "As classes são fechadas à esquerda, [li ; ls).",
              "<b>Moda:</b> para variáveis contínuas, adotou-se a <b>moda de Czuber</b>, calculada sobre as "
              "classes de Sturges: Mo = li + d₁ / (d₁ + d₂) · h. O valor mais repetido nos dados brutos é "
              "informado como referência.",
              "<b>Variância e desvio padrão amostrais</b> (divisor n − 1), porque os dias de 2025 e 2026 são uma "
              "amostra do comportamento da chuva na cidade, e não a população completa.",
              "<b>Coeficiente de variação</b> CV = s / x̄ × 100%, classificado pelo critério de Pimentel-Gomes "
              "(1985): baixo abaixo de 10%, médio de 10% a 20%, alto de 20% a 30% e muito alto a partir de 30%.",
              "<b>Quartis e percentis:</b> método padrão do pandas, interpolação linear entre as observações "
              "ordenadas (tipo 7 de Hyndman e Fan, o mesmo do QUARTIL.INC do Excel).",
          ]),
          p("4.3 Ferramentas", "h2"),
          p("Python 3.12 com pandas e NumPy (tratamento e cálculos), matplotlib (gráficos), openpyxl (planilha "
            "de entrega) e reportlab (este relatório). São seis scripts numerados que rodam em sequência e "
            "gravam todas as medidas em um único arquivo de resultados. Todos os números deste relatório são "
            "lidos desse arquivo, o que garante a rastreabilidade.")]

    # 5. Resultados --------------------------------------------------------
    c += [p("5. Resultados", "h1"),
          p("5.1 Tabela de frequências da variável discreta (Exercício 02a)", "h2"),
          p(f"A variável <i>horas_com_chuva</i> conta, em cada dia chuvoso, quantas das 24 horas tiveram "
            "precipitação maior que zero. Por ser uma contagem, é quantitativa discreta, e cada valor observado "
            "ocupa uma linha da tabela.")]
    linhas_d = [[r["horas_com_chuva"], r["fi"], br(r["fri"], 4), br(r["fri_%"]), r["Fi"], br(r["Fri"], 4),
                 br(r["Fri_%"])] for r in disc]
    linhas_d.append(["<b>Total</b>", f"<b>{tf['discreta']['soma_fi']}</b>", "<b>1,0000</b>", "<b>100,00</b>",
                     "—", "—", "—"])
    moda_d = max(disc, key=lambda r: r["fi"])
    c += [tabela("Distribuição de frequências do número de horas com chuva nos dias chuvosos",
                 ["Horas com chuva (h)", "fi", "fri", "fri (%)", "Fi", "Fri", "Fri (%)"], linhas_d,
                 [3.2 * cm] + [(LARGURA_UTIL - 3.2 * cm) / 6] * 6,
                 fonte_padrao + " Valores de 0 a 24 h não listados não ocorreram.",
                 destaque_linhas=[disc.index(moda_d)]),
          p("<b>Interpretação.</b> O valor mais frequente é de "
            f"<b>{moda_d['horas_com_chuva']} horas</b> ({moda_d['fi']} dias, {br(moda_d['fri_%'])}%). A frequência "
            f"acumulada mostra que {br(linha_disc[4]['Fri_%'])}% dos dias chuvosos tiveram até 4 horas de chuva e "
            f"{br(linha_disc[9]['Fri_%'])}% tiveram até 9 horas. Dias com chuva durante quase o dia todo são raros: "
            f"o máximo foi {disc[-1]['horas_com_chuva']} horas, em um único dia. Para o problema, isso indica que a chuva em São "
            "Paulo vem, na maior parte das vezes, em <b>pancadas de poucas horas</b>. Um alerta útil precisa, "
            "portanto, reagir na escala de horas, e não de dias.")]

    c += [p("5.2 Tabela de frequências da variável contínua (Exercício 02b)", "h2"),
          p(f"A variável <i>chuva_dia_mm</i> é contínua e foi agrupada em classes. Com n = {st['n']} dias "
            f"chuvosos, a regra de Sturges dá k = 1 + 3,322·log₁₀({st['n']}) = {br(st['k_bruto'], 2)}, "
            f"arredondado para <b>{st['k']} classes</b>. A amplitude total é AT = {br(st['maximo'], 1)} − "
            f"{br(st['minimo'], 1)} = {br(st['amplitude_total'], 1)} mm, e a amplitude de classe é "
            f"h = AT / k = {br(st['h_bruto'], 2)}, arredondada para cima para <b>h = {br(st['h'], 1)} mm</b>. "
            f"O limite inferior da primeira classe é o valor mínimo, {br(st['minimo'], 1)} mm.")]
    linhas_c = [[r["classe"].replace(".", ","), br(r["xi"]), r["fi"], br(r["fri"], 4), br(r["fri_%"]), r["Fi"],
                 br(r["Fri"], 4), br(r["Fri_%"])] for r in cont]
    linhas_c.append(["<b>Total</b>", "—", f"<b>{tf['continua']['soma_fi']}</b>", "<b>1,0000</b>",
                     "<b>100,00</b>", "—", "—", "—"])
    c += [tabela("Distribuição de frequências da precipitação diária nos dias chuvosos (mm)",
                 ["Classe (mm)", "xi (mm)", "fi", "fri", "fri (%)", "Fi", "Fri", "Fri (%)"], linhas_c,
                 [3.0 * cm, 1.9 * cm] + [(LARGURA_UTIL - 4.9 * cm) / 6] * 6, fonte_padrao,
                 destaque_linhas=[0]),
          p(f"<b>Interpretação.</b> A primeira classe concentra <b>{br(cont[0]['fri_%'])}%</b> dos dias chuvosos, e as "
            f"três primeiras somam {br(cont[2]['Fri_%'])}%. Duas classes intermediárias ficaram vazias, e a "
            f"última contém apenas o evento de {data_br(maior['data'])} ({br(maior['chuva_dia_mm'], 1, 'mm')}). "
            "Essa forma não é um erro de agrupamento: é uma característica conhecida da chuva, que tem muitos "
            "dias de pouco volume e raros eventos muito volumosos (distribuição com cauda longa à direita). "
            "Como as classes de Sturges têm largura igual, a cauda longa obriga a usar classes largas, o que "
            "reduz o detalhe na faixa onde está a maioria dos dias. É justamente na cauda, porém, que estão os "
            "eventos capazes de causar alagamentos.")]

    c += [p("5.3 Gráfico 1: histograma da precipitação diária (Exercício 03)", "h2"),
          figura(PASTA_GRAFICOS / "fig1_histograma_chuva_diaria.png",
                 "Histograma da precipitação diária nos dias chuvosos, com média, mediana e P95", fonte_padrao),
          p(f"<b>Interpretação.</b> O histograma usa as mesmas {st['k']} classes da Tabela 4 e mostra a assimetria "
            f"à direita: a barra mais alta está no início do eixo e as demais decrescem rapidamente. As linhas "
            f"verticais tornam a assimetria visível: a mediana ({br(V['mediana'], 2, 'mm')}) fica à esquerda "
            f"da média ({br(V['media'], 2, 'mm')}), porque poucos valores muito altos puxam a média para a "
            f"direita. A linha do P95 ({br(V['P95'], 2, 'mm')}) separa os {V['n_acima_P95']} dias de maior volume "
            f"({br(D['pct_dias_chuvosos_acima']['chuva_dia_mm']['P95'])}% dos dias chuvosos). Para o aplicativo, "
            "a mediana descreve melhor um dia de chuva típico do que a média.")]

    meses_secos = [r for r in mensal if r["mes"] in (7, 8)]
    c += [p("5.4 Gráfico 2: precipitação total por mês (Exercício 03)", "h2"),
          figura(PASTA_GRAFICOS / "fig2_precipitacao_mensal.png",
                 "Precipitação total por mês, de janeiro de 2025 a outubro de 2026", fonte_padrao),
          p(f"<b>Interpretação.</b> O gráfico mostra a sazonalidade da chuva em São Paulo. O mês mais chuvoso da "
            f"série foi {MESES_EXTENSO[mes_max['mes'] - 1]} de {mes_max['ano']} ({br(mes_max['chuva_total_mm'], 2, 'mm')}) "
            f"e o mais seco, {MESES_EXTENSO[mes_min['mes'] - 1]} de {mes_min['ano']} ({br(mes_min['chuva_total_mm'], 2, 'mm')}). "
            "Julho e agosto tiveram no máximo "
            f"{br(max(r['chuva_total_mm'] for r in meses_secos), 2, 'mm')} nos dois anos, enquanto o verão "
            f"(dezembro a março) reuniu {br(verao['pct_da_chuva_total'])}% de toda a chuva medida. Chama atenção "
            "que setembro e outubro de 2026 estiveram entre os meses mais chuvosos da série, o que mostra que "
            "a primavera também pode trazer volumes altos. As barras hachuradas indicam meses com dias "
            "descartados (dezembro de 2025, setembro e outubro de 2026) ou o último mês publicado. O total "
            "desses meses pode estar <b>subestimado</b>.")]

    c += [figura(PASTA_GRAFICOS / "fig3_boxplot_pico_por_mes.png",
                 "Gráfico complementar: intensidade máxima horária nos dias chuvosos, por mês do calendário",
                 fonte_padrao + " Novembro e dezembro só têm dados de 2025."),
          p("<b>Interpretação.</b> Este gráfico complementar (não substitui os dois anteriores) mostra que os "
            "picos horários mais altos e mais dispersos acontecem de janeiro a abril e em outubro, meses com "
            "caixas mais altas e com mais valores atípicos. No inverno, os picos raramente passam de 10 mm/h.")]

    def linhas_medidas(M, u):
        cz = M["detalhe_czuber"]
        return [
            ["a) Tendência central", "Média (x̄)", br(M["media"], 2, u)],
            ["", "Mediana (Md)", br(M["mediana"], 2, u)],
            ["", "Moda de Czuber (Mo)", f"{br(M['moda_czuber'], 2, u)} — classe modal "
                                       f"{cz['classe_modal'].replace('.', ',')}"],
            ["", "Valor mais frequente (dados brutos)",
             f"{', '.join(br(v, 2, u) for v in M['moda_bruta'])} ({M['moda_bruta_frequencia']} dias)"],
            ["b) Dispersão", "Máximo", br(M["maximo"], 2, u)],
            ["", "Mínimo", br(M["minimo"], 2, u)],
            ["", "Amplitude total", br(M["amplitude"], 2, u)],
            ["", "Variância amostral (s²)", br(M["variancia"], 2, f"({u})²" if "/" in u else f"{u}²")],
            ["", "Desvio padrão (s)", br(M["desvio_padrao"], 2, u)],
            ["", "Coeficiente de variação (CV)", f"{br(M['cv_pct'])}% — {M['cv_classificacao']}"],
            ["c) Separatrizes", "Q1 (25%)", br(M["Q1"], 2, u)],
            ["", "Q2 (50%, mediana)", br(M["Q2"], 2, u)],
            ["", "Q3 (75%)", br(M["Q3"], 2, u)],
            ["", "Amplitude interquartil (AIQ)", br(M["AIQ"], 2, u)],
            ["Extras", "P90 / P95 / P99", f"{br(M['P90'], 2, u)} / {br(M['P95'], 2, u)} / {br(M['P99'], 2, u)}"],
            ["", "Coeficiente de assimetria", br(M["assimetria"])],
            ["", "Valores atípicos (acima de Q3 + 1,5·AIQ)",
             f"{M['n_atipicos_acima']} dias (acima de {br(M['limite_superior_atipicos'], 2, u)})"],
        ]

    larg_med = [3.0 * cm, 5.6 * cm, LARGURA_UTIL - 8.6 * cm]
    cz_v = V["detalhe_czuber"]
    c += [tabela(f"Estatística descritiva da precipitação diária nos dias chuvosos (n = {V['n']})",
                 ["Grupo", "Medida", "Valor"], linhas_medidas(V, "mm"), larg_med, fonte_padrao, ["e", "e", "e"],
                 antes=[p("5.5 Análise univariada 1: volume diário de chuva (Exercício 04)", "h2")]),
          p(f"<b>Tendência central.</b> A média ({br(V['media'], 2, 'mm')}) é bem maior que a mediana "
            f"({br(V['mediana'], 2, 'mm')}): metade dos dias chuvosos teve até {br(V['mediana'], 2, 'mm')}, e a "
            "média é inflada por poucos dias muito chuvosos. A moda de Czuber "
            f"(Mo = {br(cz_v['li'], 1)} + {cz_v['d1']} / ({cz_v['d1']} + {cz_v['d2']}) × {br(cz_v['h'], 1)} = "
            f"{br(V['moda_czuber'], 2, 'mm')}) fica acima da mediana. Isso acontece porque a classe modal é "
            f"larga (h = {br(cz_v['h'], 1)} mm) e contém a maior parte dos dados, o que limita a precisão da "
            f"moda por classes. O valor mais repetido nos dados brutos ({br(V['moda_bruta'][0], 2, 'mm')}) "
            "confirma que a maior concentração está nos volumes pequenos."),
          p(f"<b>Dispersão.</b> O desvio padrão ({br(V['desvio_padrao'], 2, 'mm')}) é maior que a própria média, "
            f"e o CV de {br(V['cv_pct'])}% classifica a variável como de <b>{V['cv_classificacao']}</b>. Na prática, "
            "a média sozinha não descreve um dia de chuva em São Paulo: o volume varia de "
            f"{br(V['minimo'], 2, 'mm')} a {br(V['maximo'], 2, 'mm')} (amplitude de {br(V['amplitude'], 2, 'mm')})."),
          p(f"<b>Separatrizes.</b> Metade central dos dias chuvosos ficou entre Q1 = {br(V['Q1'], 2, 'mm')} e "
            f"Q3 = {br(V['Q3'], 2, 'mm')} (AIQ de {br(V['AIQ'], 2, 'mm')}). Estar acima do Q3 significa estar entre "
            f"os 25% de dias chuvosos mais volumosos ({V['n_acima_Q3']} dias, cerca de "
            f"{br(D['dias_por_ano_acima']['chuva_dia_mm']['Q3'], 1)} por ano). Acima do P95 "
            f"({br(V['P95'], 2, 'mm')}) ficaram {V['n_acima_P95']} dias, cerca de "
            f"{br(D['dias_por_ano_acima']['chuva_dia_mm']['P95'], 1)} por ano. Pelo critério de Tukey, há "
            f"{V['n_atipicos_acima']} dias atípicos, com mais de {br(V['limite_superior_atipicos'], 2, 'mm')}.")]

    cz_i = I["detalhe_czuber"]
    c += [tabela(f"Estatística descritiva do pico de precipitação horária nos dias chuvosos (n = {I['n']})",
                 ["Grupo", "Medida", "Valor"], linhas_medidas(I, "mm/h"), larg_med,
                 fonte_padrao + f" Classes de Sturges próprias desta variável: k = {cz_i['sturges']['k']}, "
                 f"h = {br(cz_i['h'], 1)} mm/h, a partir de {br(cz_i['sturges']['minimo'], 1)} mm/h.",
                 ["e", "e", "e"],
                 antes=[p("5.6 Análise univariada 2: intensidade máxima horária (Exercício 04)", "h2")]),
          p(f"<b>Tendência central.</b> Em um dia chuvoso típico, a hora mais intensa teve "
            f"{br(I['mediana'], 2, 'mm/h')} (mediana), enquanto a média é {br(I['media'], 2, 'mm/h')}. A razão "
            f"média/mediana ({br(D['razao_media_mediana']['pico_mm_h'])}) é ainda maior que a do volume diário, e "
            f"o coeficiente de assimetria ({br(I['assimetria'])}) também. A intensidade é, portanto, a variável "
            f"mais concentrada em poucos eventos extremos. A moda de Czuber ({br(I['moda_czuber'], 2, 'mm/h')}) "
            "fica dentro da primeira classe, como no volume diário."),
          p(f"<b>Dispersão.</b> O CV de {br(I['cv_pct'])}% ({I['cv_classificacao']}) é o maior das duas "
            f"variáveis. O máximo de {br(I['maximo'], 2, 'mm/h')} é mais de "
            f"{int(I['maximo'] // I['P99'])} vezes o P99 ({br(I['P99'], 2, 'mm/h')}): um evento muito fora "
            "do padrão do restante da série."),
          p(f"<b>Separatrizes.</b> Um quarto dos dias chuvosos teve pico acima de Q3 = {br(I['Q3'], 2, 'mm/h')}. "
            f"O limite de Tukey para atípicos ({br(I['limite_superior_atipicos'], 2, 'mm/h')}) fica muito próximo "
            f"do P95 ({br(I['P95'], 2, 'mm/h')}), e os {I['n_atipicos_acima']} dias atípicos coincidem em número "
            f"com os {I['n_acima_P95']} dias acima do P95. São esses dias que o aplicativo deve tratar como "
            "eventos de alto risco.")]

    # 6. Insights ----------------------------------------------------------
    dpa = D["dias_por_ano_acima"]["pico_mm_h"]
    meses_risco = sorted(ins["por_mes"], key=lambda r: (-r["dias_pico_acima_P90"], -r["pico_max_mm_h"]))[:4]
    texto_meses = "; ".join(f"{r['mes_nome']}: {r['dias_pico_acima_P90']} dias" for r in meses_risco)
    horas_ord = sorted([(h, q) for h, q in hp["contagem_por_hora"].items() if q >= 3], key=lambda kv: -kv[1])
    c += [p("6. Insights para a solução", "h1"),
          p("6.1 Por que a intensidade horária é o melhor gatilho", "h2"),
          p(f"O volume diário mistura situações muito diferentes: {br(maior['chuva_dia_mm'], 1, 'mm')} distribuídos "
            "ao longo do dia são absorvidos pela drenagem, mas a mesma quantidade em uma hora não é. Os dados "
            f"mostram isso: na mediana, {br(ins['fracao_do_dia_na_hora_de_pico_pct']['mediana'])}% da chuva de "
            f"um dia chuvoso cai em uma única hora. Dos {ivv['dias_pico_acima_P95']} dias com pico acima do P95 "
            f"da intensidade, <b>{ivv['destes_com_volume_ate_P95_diario']} não seriam detectados</b> por um "
            f"limiar no P95 do volume diário. Além disso, a intensidade horária pode ser medida e transmitida em "
            "tempo real, enquanto o total diário só é conhecido quando o dia termina.")]
    linhas_lim = [
        ["Atenção", "P90", br(I["P90"], 2, "mm/h"), f"{I['n_acima_P90']} ({br(D['pct_dias_chuvosos_acima']['pico_mm_h']['P90'])}%)",
         br(dpa["P90"], 1)],
        ["Alerta", "P95", br(I["P95"], 2, "mm/h"), f"{I['n_acima_P95']} ({br(D['pct_dias_chuvosos_acima']['pico_mm_h']['P95'])}%)",
         br(dpa["P95"], 1)],
        ["Alerta máximo", "P99", br(I["P99"], 2, "mm/h"), f"{I['n_acima_P99']} ({br(D['pct_dias_chuvosos_acima']['pico_mm_h']['P99'])}%)",
         br(dpa["P99"], 1)],
    ]
    c += [tabela("Limiares de alerta baseados nos percentis da intensidade máxima horária",
                 ["Nível", "Percentil", "Chuva em 1 hora acima de", "Dias chuvosos acima (n e %)",
                  "Dias por ano (aprox.)"],
                 linhas_lim, [2.8 * cm, 2.0 * cm, 3.8 * cm, 4.2 * cm, LARGURA_UTIL - 12.8 * cm], fonte_padrao +
                 f" Dias por ano = nº de dias acima ÷ ({t['dias_validos']} dias válidos ÷ 365,25).",
                 antes=[p("6.2 Limiares de alerta propostos", "h2")]),
          p("Esses limiares são <b>estatísticos</b>, derivados apenas desta série, e não são classificações "
            "oficiais da Defesa Civil, do CGE ou do INMET. A escala de três níveis equilibra sensibilidade e "
            f"incômodo: o nível de atenção seria acionado em cerca de {br(dpa['P90'], 1)} dias por ano, um "
            "volume baixo o suficiente para o usuário não ignorar os avisos. O volume diário pode servir como "
            f"gatilho secundário, acima do P95 ({br(V['P95'], 2, 'mm')}), para chuvas longas que saturam o solo "
            "e elevam rios mesmo sem picos intensos.")]
    c += [p("6.3 Épocas e horários de maior risco", "h2"),
          *lista([
              f"<b>Meses:</b> os dias com pico acima do P90 se concentram em {texto_meses}. De dezembro a março "
              f"estão {verao['dias_pico_acima_P90']} dos {verao['total_dias_pico_acima_P90']} dias "
              f"({br(verao['pct_dos_dias_pico_acima_P90'])}%). O aplicativo pode reforçar o monitoramento e as "
              "notificações preventivas nesse período, mas não deve desligá-las no resto do ano, como mostram "
              "setembro e outubro de 2026.",
              f"<b>Horários:</b> nos {hp['n_dias']} dias com pico acima do P90, {hp['n_entre_14h_e_21h']} picos "
              f"({br(hp['pct_entre_14h_e_21h'])}%) ocorreram entre 14h e 21h no horário de Brasília. As horas mais "
              "frequentes (3 dias ou mais) foram " + " e ".join(f"{h}h ({q} dias)" for h, q in horas_ord) + ". A amostra é "
              "pequena, mas sugere atenção especial ao fim da tarde, quando coincide com o horário de pico do "
              "trânsito.",
              f"<b>Duração:</b> como {br(linha_disc[4]['Fri_%'])}% dos dias chuvosos têm até 4 horas de chuva, "
              "o aplicativo deve recalcular as rotas na escala de horas e retirar os alertas pouco tempo depois "
              "do fim da chuva forte.",
          ])]

    # 7. Limitações --------------------------------------------------------
    c += [p("7. Limitações", "h1"),
          *lista([
              "<b>Uma única estação:</b> a A701 representa as condições da Zona Norte e não mede a chuva em cada "
              "rua. Tempestades de verão são localizadas e podem atingir um bairro sem atingir o pluviômetro.",
              f"<b>Série curta:</b> são cerca de {br(D['anos_equivalentes_de_dados'], 1)} anos de dados. Os percentis "
              "extremos, sobretudo o P99, são estimados com poucos eventos e podem mudar com mais anos de série.",
              f"<b>2026 parcial:</b> os dados terminam em {fim}. Novembro e dezembro aparecem só uma vez, e cinco "
              "dias foram descartados por falta de dados, o que pode subestimar os totais de dezembro de 2025 e "
              "de setembro e outubro de 2026.",
              "<b>Chuva não é alagamento:</b> esta análise não relaciona a chuva aos pontos de alagamento. O "
              "próximo passo é cruzar a série com os registros de alagamentos do Centro de Gerenciamento de "
              "Emergências Climáticas (CGE) da Prefeitura, para calibrar os limiares e estimar o risco por local.",
              "<b>Análise só univariada:</b> não se estudou a relação entre variáveis (por exemplo, intensidade × "
              "volume, ou chuva acumulada nos dias anteriores), o que exigiria análise bivariada ou modelos.",
          ])]

    # 8. Conclusão ---------------------------------------------------------
    c += [p("8. Conclusão", "h1"),
          p(f"A análise de {t['dias_validos']} dias de dados oficiais do INMET mostra que a chuva em São Paulo é "
            f"concentrada e irregular: choveu de forma relevante em {br(t['pct_dias_chuvosos'])}% dos dias, "
            "geralmente por poucas horas, e as duas variáveis analisadas têm coeficiente de variação acima de "
            "100% e forte assimetria à direita. O risco de alagamento está na cauda dessas distribuições, em "
            "poucos dias por ano com chuva muito intensa em uma ou duas horas. Por isso, a recomendação para o "
            "aplicativo é usar a <b>intensidade horária</b> como gatilho principal, com níveis de atenção, "
            f"alerta e alerta máximo em {br(I['P90'], 2, 'mm/h')}, {br(I['P95'], 2, 'mm/h')} e "
            f"{br(I['P99'], 2, 'mm/h')}, com reforço de dezembro a março e no fim da tarde. Os resultados "
            "sustentam a hipótese “chuva forte → alagamento” como ponto de partida. A validação definitiva "
            "depende de cruzar esses limiares com registros reais de alagamento e de ampliar a série para mais "
            "anos e mais estações.")]

    # 9. Referências -------------------------------------------------------
    hoje = date.today()
    acesso = f"Acesso em: {hoje.day} {['jan.', 'fev.', 'mar.', 'abr.', 'maio', 'jun.', 'jul.', 'ago.', 'set.', 'out.', 'nov.', 'dez.'][hoje.month - 1]} {hoje.year}."
    refs = [
        f"INSTITUTO NACIONAL DE METEOROLOGIA (INMET). <b>Dados Históricos Anuais</b>: estações automáticas, 2025 e 2026. "
        f"Disponível em: https://portal.inmet.gov.br/dadoshistoricos. Arquivos: "
        f"https://portal.inmet.gov.br/uploads/dadoshistoricos/2025.zip e "
        f"https://portal.inmet.gov.br/uploads/dadoshistoricos/2026.zip. {acesso}",
        "CRESPO, A. A. <b>Estatística fácil</b>. 19. ed. São Paulo: Saraiva, 2009.",
        "STURGES, H. A. The choice of a class interval. <b>Journal of the American Statistical Association</b>, "
        "v. 21, n. 153, p. 65-66, 1926.",
        "PIMENTEL-GOMES, F. <b>Curso de estatística experimental</b>. Piracicaba: Nobel, 1985.",
        "HYNDMAN, R. J.; FAN, Y. Sample quantiles in statistical packages. <b>The American Statistician</b>, "
        "v. 50, n. 4, p. 361-365, 1996.",
        "EXPERT TEAM ON CLIMATE CHANGE DETECTION AND INDICES (ETCCDI). <b>Climate change indices: definitions of the "
        "27 core indices</b>. Disponível em: http://etccdi.pacificclimate.org/list_27_indices.shtml. " + acesso,
        "PANDAS DEVELOPMENT TEAM. <b>pandas documentation</b>: pandas.Series.quantile. Disponível em: "
        "https://pandas.pydata.org/docs/reference/api/pandas.Series.quantile.html. " + acesso,
        "MATPLOTLIB DEVELOPMENT TEAM. <b>Matplotlib documentation</b>. Disponível em: https://matplotlib.org/stable/. "
        + acesso,
        "NAÇÕES UNIDAS NO BRASIL. <b>Objetivos de Desenvolvimento Sustentável</b>: ODS 11 e ODS 13. Disponível em: "
        "https://brasil.un.org/pt-br/sdgs. " + acesso,
        "PREFEITURA DE SÃO PAULO. <b>Centro de Gerenciamento de Emergências Climáticas (CGE)</b>. Disponível em: "
        "https://www.cgesp.org. " + acesso,
    ]
    c += [p("9. Referências", "h1"), *[p(r, "ref") for r in refs]]
    return c


def main():
    R = carregar_resultados()
    necessarias = ["tratamento", "tabelas_frequencia", "graficos", "estatistica_descritiva", "insights"]
    faltando = [s for s in necessarias if s not in R]
    if faltando:
        raise SystemExit(f"Seções ausentes em resultados.json: {faltando}. Rode os scripts 02 a 05 antes.")
    D = calcular_derivados(R)

    hoje = date.today()
    hoje_txt = f"{MESES_EXTENSO[hoje.month - 1]} de {hoje.year}"
    PASTA_ENTREGA.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(ARQ_PDF), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm,
        bottomMargin=2.2 * cm, title="Chuvas intensas e risco de alagamentos em São Paulo",
        author="; ".join(f"{nome} (RM {rm})" for nome, rm in INTEGRANTES),
        subject="Global Solution CitizenTech — Estatística — FIAP",
    )
    historia = capa(hoje_txt) + montar_conteudo(R, D)
    doc.build(historia, onFirstPage=desenhar_rodape, onLaterPages=desenhar_rodape)
    print(f"PDF gerado: {ARQ_PDF}  ({NUM.tabela} tabelas, {NUM.figura} figuras)")


if __name__ == "__main__":
    main()
