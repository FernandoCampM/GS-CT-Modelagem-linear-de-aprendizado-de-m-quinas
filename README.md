# Chuvas intensas e risco de alagamentos em São Paulo

**Global Solution CitizenTech · FIAP · Ciência da Computação · Estatística**

Análise estatística da precipitação horária medida pela estação automática **INMET A701
(São Paulo - Mirante de Santana)** de **01/01/2025 a 31/10/2026**. O objetivo é dar base
estatística ao aplicativo de rotas do grupo, que usa o histórico de chuvas fortes para estimar
onde vai alagar e sugerir a rota menos afetada. A análise indica **quais níveis de chuva** e
**quais épocas do ano** devem disparar alertas.

ODS relacionados: **11** (Cidades e comunidades sustentáveis) e **13** (Ação contra a mudança global do clima).

## Integrantes

| Nome completo | RM |
|---|---|
| Fernando Campos Garnica Mota | 567451 |
| André da Silva Pinto | 559038 |

## Entregáveis

A pasta [`entrega/`](entrega/) tem exatamente o que vai para o Portal:

| Arquivo | Conteúdo |
|---|---|
| [`base_chuvas_A701_2025_2026.xlsx`](entrega/base_chuvas_A701_2025_2026.xlsx) | Base de dados, com as abas `integrantes`, `dicionario`, `diaria` e `horaria` |
| [`relatorio_estatistico_GS_enchentes.pdf`](entrega/relatorio_estatistico_GS_enchentes.pdf) | Relatório estatístico (13 páginas, 7 tabelas, 3 figuras) |
| `01_baixar_dados.py` … `06_gerar_relatorio.py`, `comum.py` | Códigos em Python (cópias de `src/`) |

| Exercício | Onde está |
|---|---|
| 01 · Base real e justificativa | Relatório, seção 3 |
| 02 · Tabelas de frequência (discreta e contínua) | `03_tabelas_frequencia.py` · relatório, seções 5.1 e 5.2 |
| 03 · Dois gráficos de tipos e variáveis diferentes | `04_graficos.py` · relatório, seções 5.3 e 5.4 |
| 04 · Duas análises univariadas | `05_estatistica_descritiva.py` · relatório, seções 5.5 e 5.6 |
| 05 · Relatório com interpretação e insights | `06_gerar_relatorio.py` · relatório inteiro |
| 06 · Base, códigos e relatório | pasta `entrega/` |

## Principais resultados

Base: 664 dias válidos, dos quais 207 foram dias chuvosos (≥ 1,0 mm).

| Medida (dias chuvosos) | Volume diário | Intensidade máxima horária |
|---|---|---|
| Média | 13,66 mm | 7,05 mm/h |
| Mediana | 8,00 mm | 4,00 mm/h |
| Coeficiente de variação | 115,44% | 125,60% |
| P90 / P95 / P99 | 32,04 / 41,56 / 65,67 mm | 17,84 / 20,98 / 35,53 mm/h |

- **A chuva é muito irregular:** a média fica bem acima da mediana, e o CV passa de 100% nas duas variáveis.
- **Os eventos extremos são breves:** em 24/01/2025 caíram 82,0 mm em uma hora, 65,29% da chuva do dia.
- **A intensidade horária é um gatilho de alerta melhor que o volume diário:** dos 11 dias com pico
  acima do P95, 6 não passariam do P95 do volume diário.
- **Limiares de alerta propostos** (percentis dos dados, não são classificações oficiais):
  atenção acima de 17,84 mm/h, alerta acima de 20,98 mm/h e alerta máximo acima de 35,53 mm/h.
- **Sazonalidade:** de dezembro a março está 51,56% da chuva. Em 2026, setembro e outubro também foram muito chuvosos.

## Estrutura do projeto

```
├── CLAUDE.md                 # especificação do trabalho e estado atual (seção 0)
├── requirements.txt          # dependências com versões fixadas
├── dados/
│   ├── brutos/               # CSVs da A701 extraídos do INMET (os ZIPs não vão para o git)
│   └── processados/          # bases horária e diária tratadas
├── src/                      # scripts 01 a 06 e comum.py (fonte de verdade)
├── saidas/
│   ├── tabelas/              # tabelas de frequência em CSV
│   ├── graficos/             # figuras em PNG, 300 dpi
│   └── resultados.json       # todas as medidas calculadas (fonte única dos números do PDF)
└── entrega/                  # o que vai para o Portal
```

## Como rodar

Requer Python 3.12.

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt   # no Linux/macOS: .venv/bin/python
```

Depois, rode os scripts em ordem, a partir da raiz do projeto:

```bash
.venv/Scripts/python.exe src/01_baixar_dados.py            # baixa os ZIPs do INMET e extrai a A701
.venv/Scripts/python.exe src/02_tratar_dados.py            # trata os dados e gera o .xlsx
.venv/Scripts/python.exe src/03_tabelas_frequencia.py      # Exercício 02
.venv/Scripts/python.exe src/04_graficos.py                # Exercício 03
.venv/Scripts/python.exe src/05_estatistica_descritiva.py  # Exercício 04
.venv/Scripts/python.exe src/06_gerar_relatorio.py         # Exercício 05 (PDF)
```

Depois de alterar algum script, copie os `.py` de `src/` para `entrega/`.

## Fonte dos dados

INMET — Instituto Nacional de Meteorologia, [Dados Históricos Anuais](https://portal.inmet.gov.br/dadoshistoricos),
arquivos [2025.zip](https://portal.inmet.gov.br/uploads/dadoshistoricos/2025.zip) e
[2026.zip](https://portal.inmet.gov.br/uploads/dadoshistoricos/2026.zip). O arquivo de 2026 é parcial
e vai até 31/10/2026.

Principais decisões de tratamento: horário convertido de UTC para Brasília (UTC−3), dia válido só com
pelo menos 20 das 24 horas com dado (5 dias descartados) e dia chuvoso com precipitação ≥ 1,0 mm.
Os detalhes e as justificativas estatísticas estão na seção 4 do relatório.
