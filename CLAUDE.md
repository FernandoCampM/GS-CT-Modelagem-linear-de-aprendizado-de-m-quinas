# CLAUDE.md — GS CitizenTech · Estatística (Ciência da Computação, 3º semestre)

Você vai ajudar a fazer a parte de **Estatística** da Global Solution CitizenTech da FIAP.
Leia este arquivo inteiro antes de começar e siga as fases em ordem. Ao fim de cada fase,
mostre o que foi gerado e espere o "ok" antes de seguir.

---

## 0. ESTADO ATUAL: trabalho concluído, em fase de REVISÃO (atualizado em 16/11/2026)

> **Para o próximo Claude:** as 7 fases abaixo (seção 5) **já foram feitas** e aprovadas uma a uma
> pelo usuário. A lista de integrantes foi confirmada. **Não refaça o trabalho do zero.**
> O usuário vai revisar em outro computador. Seu papel agora é ajudar nessa revisão: explicar
> decisões, corrigir o que ele pedir, regenerar as saídas e atualizar `entrega/`.
> As seções 1 a 7 continuam valendo como especificação e regras do trabalho.

### 0.1 O que existe
- `entrega/` (o que vai para o Portal, 9 arquivos): `base_chuvas_A701_2025_2026.xlsx`,
  `01_baixar_dados.py` … `06_gerar_relatorio.py`, `comum.py` e
  `relatorio_estatistico_GS_enchentes.pdf` (13 páginas, 7 tabelas, 3 figuras).
- `src/`: os mesmos `.py` (fonte de verdade). Os de `entrega/` são **cópias**; depois de mudar
  qualquer script, copie de novo (`cp src/0*.py src/comum.py entrega/`).
- `src/comum.py`: módulo extra (não estava na especificação). Guarda caminhos, integrantes, fonte,
  leitura/gravação de `resultados.json`, a regra de Sturges e a montagem das tabelas de classes.
  Também força a saída do terminal em UTF-8 (sem isso, os scripts 03 e 05 quebravam no Windows
  ao imprimir Σ e →).
- `saidas/resultados.json`: fonte única dos números. Seções: `tratamento`, `tabelas_frequencia`,
  `graficos`, `estatistica_descritiva`, `insights`, `derivados_relatorio` (esta é gravada pelo 06).
- `dados/brutos/`: os ZIPs do INMET (~170 MB) e os CSVs da A701 extraídos. Se não vierem para o
  outro PC, o script 01 baixa de novo.

### 0.2 Como rodar em outro computador
1. Python 3.12 (no PC original foi instalado via `winget install -e --id Python.Python.3.12`).
2. O `.venv` **não é portátil**: apague e recrie.
   `python -m venv .venv` e depois `.venv/Scripts/python.exe -m pip install -r requirements.txt`
   (versões fixadas; inclui `truststore`, ver 0.3).
3. Rodar em ordem, da raiz do projeto: `python src/01_baixar_dados.py` até `python src/06_gerar_relatorio.py`.
   Todos rodam do zero sem erro (testado com as saídas apagadas).
4. Para revisar o PDF visualmente, foi usado `pymupdf` (instalado só no venv, fora do
   `requirements.txt`) para renderizar as páginas em PNG.

### 0.3 Decisões e desvios em relação a esta especificação
- **Download:** o servidor do INMET exige User-Agent de navegador, e o Python recusava o certificado
  ("self-signed certificate in chain"). Solução: `truststore` (usa os certificados do Windows; a
  verificação continua ligada). Não desligue a verificação SSL.
- **Formato real do CSV:** hora `0000 UTC` nos dois anos (o código aceita também `00:00`), data
  `2025/01/01`, faltantes vêm vazios. 19 colunas, mesmos nomes nos dois anos.
- **Período:** 01/01/2025 a **31/10/2026** (último registro publicado: 31/10/2026 23h UTC = 20h local).
- **Fuso:** UTC−3 fixo. A conversão gera 3 h em 31/12/2024, removidas como "fora do período"
  (não contam como dias descartados).
- **Dias descartados (< 20 h):** 5 — 02/12/2025, 14/09/2026, 15/09/2026, 21/10/2026, 26/10/2026.
  Nesses dias as medidas de chuva ficam vazias. O último dia (31/10) tem 21 h e é válido.
- **Critério do CV:** a especificação sugeria baixa/média/alta; não foi possível confirmar a fonte do
  critério 15%/30% (atribuído a Martins). Usou-se **Pimentel-Gomes (1985)**: < 10% baixa, 10–20% média,
  20–30% alta, ≥ 30% muito alta. As duas variáveis dão "muito alta" (CV > 100%) em qualquer critério.
- **Dia chuvoso ≥ 1,0 mm:** citado como índice de dias úmidos do ETCCDI.
- **Premissa não confirmada:** o valor horário do INMET foi tratado como a chuva da hora que
  **termina** no horário indicado. Não achei documentação oficial; está como premissa no relatório
  (só afeta a análise da hora do pico, seção 6.3 do PDF).
- **Limiares de alerta:** só percentis dos dados (P90/P95/P99 de `pico_mm_h` = 17,84 / 20,98 /
  35,53 mm/h). Nenhuma classificação oficial (Defesa Civil, CGE, INMET) foi usada.
- **Gráficos:** os títulos das imagens não têm "Figura N" (o PDF numera nas legendas). Há um
  3º gráfico extra (boxplot de `pico_mm_h` por mês).

### 0.4 Números-chave (para conferência rápida; a fonte é `resultados.json`)
664 dias válidos, 207 chuvosos (31,17%), 133 horas faltantes de 16.053. Volume diário: média
13,66 mm, mediana 8,00 mm, CV 115,44%, P95 41,56 mm. Pico horário: média 7,05 mm/h, mediana
4,00 mm/h, CV 125,60%. Maior evento: 24/01/2025, 125,6 mm no dia e 82,0 mm em uma hora.
Dos 11 dias com pico > P95, 6 não passariam do P95 do volume diário.

### 0.5 Pontos que o usuário ainda quer revisar / possíveis melhorias
- Ler o PDF inteiro (ele precisa defender o trabalho; pontos sensíveis: moda de Czuber acima da
  mediana na seção 5.5 e os limiares da seção 6.2).
- Conferir na fonte original as referências clássicas: Crespo (2009), Sturges (1926),
  Hyndman & Fan (1996), Pimentel-Gomes (1985).
- Melhorias opcionais anotadas: a Figura 2 fica pequena no PDF (rótulos difíceis de ler); a nota
  de fonte aparece duas vezes (dentro da imagem e embaixo da figura).
- Nada foi enviado ao Portal; o envio é do usuário.
- **Repositório git:** https://github.com/FernandoCampM/GS-CT-Modelagem-linear-de-aprendizado-de-m-quinas
  (público, branch `main`). Os ZIPs do INMET ficam fora do git (`.gitignore`); os CSVs da A701 extraídos
  estão versionados. `.gitattributes` marca CSV/JSON como `-text` para não alterar os bytes dos dados.
  No outro PC: `git clone` do link acima e siga a seção 0.2. Faça commit/push só quando o usuário pedir.
- A pasta local no PC original se chamava `GSPROMPT`; o usuário pediu para renomeá-la para `GSModelagem`
  (feito por ele, fora da sessão). Nenhum arquivo depende do nome da pasta.

### 0.6 Regras ao fazer alterações na revisão
- Mude em `src/`, rode os scripts afetados **e todos os seguintes** (o 06 sempre por último),
  copie para `entrega/` e confira que os números do PDF batem com `resultados.json`.
- Mantenha cabeçalho com nome e RM em todo `.py` novo ou alterado.
- Não invente números, limiares oficiais nem fontes (regra da seção 5, Fase 6).

---

## 1. Contexto do projeto

- **Tema da GS:** CitizenTech, ou seja, tecnologia criada a partir de necessidades reais das pessoas.
- **Problema escolhido pelo grupo:** **enchentes e alagamentos em São Paulo**.
- **Solução do grupo (de outras matérias, para dar contexto):** um app parecido com o Google Maps.
  Ele usa o histórico de chuvas fortes para estimar onde vai alagar e calcula a rota
  menos afetada para o usuário, a pé e de carro.
- **Papel desta entrega:** a análise estatística das chuvas, que dá a base para a hipótese do app
  ("chuva forte → alagamento"). Também indica quais níveis de chuva e quais épocas do ano
  devem disparar alertas. Esta entrega **não** implementa o app nem as rotas.
- **ODS relacionados:** 11 (Cidades e comunidades sustentáveis) e 13 (Ação contra a mudança do clima).

### Integrantes (aparecem em TODOS os entregáveis)
| Nome completo | RM |
|---|---|
| Fernando Campos Garnica Mota | 567451 |
| André da Silva Pinto | 559038 |

> ⚠️ Antes da fase final, peça para o usuário confirmar se a lista de integrantes está correta.

---

## 2. Enunciado (o que o professor pede)

**Orientações gerais**
- Todos os entregáveis têm que trazer o **nome completo e o RM de todos os integrantes**.
- Nada de links. Os arquivos vão direto no Portal, nos formatos pedidos.
- **Cada item ausente ou não atendido desconta 1,0 ponto.**

**Exercícios**
- **01:** Usar uma base real (IBGE, dados.gov.br, Kaggle etc.) e justificar a escolha.
  Bases artificiais ou fictícias não são aceitas.
- **02 (2,0):** Tabela de Distribuição de Frequências em Python para
  a) 1 variável quantitativa **discreta** e b) 1 variável quantitativa **contínua**.
- **03 (2,0):** **Dois gráficos diferentes**, com **variáveis diferentes**, e todos os elementos:
  título, rótulos dos eixos x e y, cor, legenda/fonte e o que mais o tipo de gráfico pedir.
- **04 (2,0):** **Duas análises univariadas** com estatística descritiva:
  a) média, mediana e moda;
  b) máximo, mínimo, amplitude, variância, desvio padrão e coeficiente de variação;
  c) quartis.
- **05 (2,0):** Relatório estatístico com tabelas, gráficos e medidas, **cada um com interpretação**,
  tirando insights para o problema-tema. O tom é de relatório profissional para um cliente,
  que vai avaliar também o rigor técnico.
- **06:** Entregar a) base em **.csv ou .xlsx**, b) códigos em **.py** e c) relatório em **.pdf**.

---

## 3. Base de dados

- **Fonte:** INMET, Dados Históricos Anuais das estações automáticas.
- **Estação:** **A701, São Paulo - Mirante de Santana** (Zona Norte de SP).
- **Período:** **2025 e 2026**. O arquivo de 2026 é parcial, vai até o mês mais recente publicado
  pelo INMET. Descubra a última data disponível e cite no relatório.
- **Links:**
  - https://portal.inmet.gov.br/uploads/dadoshistoricos/2025.zip
  - https://portal.inmet.gov.br/uploads/dadoshistoricos/2026.zip
- Cada ZIP tem um CSV para cada estação do Brasil. Extraia **só** o arquivo que tem `A701` no nome.
- Se o download falhar (rede, bloqueio, timeout), **pare e peça para o usuário baixar manualmente**
  e colocar os ZIPs em `dados/brutos/`. **Nunca invente, simule ou complete dados.**

### Formato esperado do CSV do INMET (confira no arquivo, não confie cegamente)
- As primeiras linhas (~8) são **metadados** da estação (região, UF, nome, código, lat/long,
  altitude, data de fundação). Leia e guarde esses metadados, porque vão para o relatório.
- Separador `;`, decimal `,` e encoding provavelmente `latin-1`.
- Coluna de chuva parecida com `PRECIPITAÇÃO TOTAL, HORÁRIO (mm)`.
- Data e hora em colunas como `Data` e `Hora UTC`. O formato da hora mudou entre anos,
  algo como `0000 UTC` ou `00:00`. Trate os dois casos.
- Valores faltantes podem vir como `-9999` ou vazios.

---

## 4. Estrutura de pastas

```
gs-estatistica/
├── CLAUDE.md
├── requirements.txt          # pandas, numpy, matplotlib, openpyxl, reportlab, requests
├── dados/
│   ├── brutos/               # ZIPs e CSVs originais da A701 (não alterar)
│   └── processados/
├── src/
│   ├── 01_baixar_dados.py
│   ├── 02_tratar_dados.py
│   ├── 03_tabelas_frequencia.py
│   ├── 04_graficos.py
│   ├── 05_estatistica_descritiva.py
│   └── 06_gerar_relatorio.py
├── saidas/
│   ├── tabelas/              # CSVs das tabelas de frequência
│   ├── graficos/             # PNGs em 300 dpi
│   └── resultados.json       # todas as medidas calculadas (fonte única dos números)
└── entrega/                  # SÓ o que vai para o Portal
```

Regras de código:
- Use `pathlib` para os caminhos. Tudo tem que rodar de novo do zero com `python src/0X_....py`.
- **Cada `.py` começa com um cabeçalho** com disciplina, "Global Solution CitizenTech",
  nome completo e RM dos integrantes e uma descrição do script.
- Código e comentários em português, com nomes de variáveis claros. Comente as decisões
  estatísticas (por que Sturges, por que variância amostral etc.).
- Crie um `.venv` e um `requirements.txt`. Instale as dependências só depois de mostrar o que vai instalar.

---

## 5. Fases de trabalho

### Fase 1: Download e extração (`01_baixar_dados.py`)
1. Baixar os dois ZIPs para `dados/brutos/`, pulando os que já existirem.
2. Extrair só o CSV da A701 de cada ZIP.
3. Imprimir os metadados da estação e as primeiras linhas de dados de cada arquivo.
✅ Checkpoint: mostrar os nomes dos arquivos, as colunas e a primeira e a última data de cada ano.

### Fase 2: Tratamento (`02_tratar_dados.py`)
1. Ler os dois CSVs pulando os metadados e padronizar nomes de colunas, tipos e decimais.
2. Converter `-9999` e vazios em `NaN`. Ficar só com data, hora e precipitação.
   As outras colunas podem ficar na base horária completa, se for útil.
3. Montar um datetime em UTC e **converter para horário de Brasília (UTC-3)**
   antes de agregar por dia.
4. **Base horária** (`chuva_A701_horaria.csv`): datetime_local, data, hora, precipitacao_mm.
5. **Base diária** (`chuva_A701_diaria.csv`), com uma linha por dia:
   - `chuva_dia_mm`: soma do dia (**contínua**)
   - `horas_com_chuva`: nº de horas com precipitação > 0 (**discreta**, de 0 a 24)
   - `pico_mm_h`: maior valor horário do dia (**contínua**, mede a intensidade)
   - `horas_validas`: nº de horas sem `NaN`
   - `mes`, `ano`, `dia_chuvoso` (chuva_dia_mm ≥ 1,0 mm, critério climatológico de "dia de chuva")
6. Regra de qualidade: o dia só é válido se tiver **pelo menos 20 das 24 horas** com dado.
   Conte quantos dias foram descartados e registre em `resultados.json`.
7. Gerar o **arquivo de entrega da base** em `.xlsx` (`entrega/base_chuvas_A701_2025_2026.xlsx`), com as abas:
   - `integrantes`: nomes, RMs, disciplina e fonte dos dados com o link
   - `dicionario`: cada coluna com descrição, unidade e tipo (discreta ou contínua)
   - `diaria` e `horaria`
   (O `.xlsx` resolve a exigência de nome e RM em todos os entregáveis, coisa que um CSV puro não resolve.)
✅ Checkpoint: período coberto, nº de dias válidos e descartados, nº de dias chuvosos
e as 5 maiores chuvas diárias.

### Fase 3: Tabelas de frequência, Ex. 02 (`03_tabelas_frequencia.py`)
- **a) Discreta: `horas_com_chuva`**, só nos dias chuvosos (explique o motivo).
  Uma linha por valor, com fi, fri, fri%, Fi, Fri e Fri%.
- **b) Contínua: `chuva_dia_mm`**, só nos dias chuvosos.
  - Número de classes pela **regra de Sturges** (k = 1 + 3,322·log₁₀ n), com AT, h e limites
    mostrados no código e no relatório.
  - Classes fechadas à esquerda `[li, ls)`, com ponto médio xi, fi, fri, fri%, Fi, Fri e Fri%.
  - A cauda longa deve deixar quase tudo na 1ª classe. Explique isso no relatório
    como característica real da chuva, não como erro.
- Conferir que Σfi = n e Σfri = 1. Salvar em `saidas/tabelas/` e também como imagem ou tabela formatada para o PDF.
✅ Checkpoint: mostrar as duas tabelas no terminal.

### Fase 4: Gráficos, Ex. 03 (`04_graficos.py`)
Dois gráficos de **tipos diferentes** e **variáveis diferentes**:
1. **Histograma de `chuva_dia_mm`** (dias chuvosos), com as mesmas classes da tabela contínua
   e linhas verticais marcando média, mediana e P95.
2. **Gráfico de barras da precipitação total por mês** (soma de `chuva_dia_mm`),
   uma barra por mês e ano, de jan/2025 até o último mês de 2026. Marque visualmente
   que o último mês de 2026 pode estar incompleto.
- Opcional (extra, não substitui os dois acima): boxplot de `pico_mm_h` por mês.
- Elementos obrigatórios em todos: **título, rótulo do eixo x com unidade, rótulo do eixo y
  com unidade, cor definida, legenda quando houver mais de uma série, grade leve e
  nota de fonte** ("Fonte: INMET, estação A701, 2025–2026").
- Salvar em PNG a 300 dpi em `saidas/graficos/`.
✅ Checkpoint: mostrar os arquivos gerados para o usuário abrir.

### Fase 5: Estatística descritiva, Ex. 04 (`05_estatistica_descritiva.py`)
Duas análises univariadas, nos **dias chuvosos**:
1. `chuva_dia_mm` (volume diário)
2. `pico_mm_h` (intensidade máxima horária)

Para cada uma, calcular:
- **a) Tendência central:** média, mediana e moda. Para variável contínua, informe a **moda
  da distribuição em classes (Czuber)**, explique a escolha e mostre também o valor mais
  frequente dos dados brutos, se fizer sentido.
- **b) Dispersão:** máximo, mínimo, amplitude, **variância amostral (ddof=1)**,
  desvio padrão e **CV = s / x̄ × 100%**. Classifique o CV (baixa, média ou alta dispersão)
  e cite o critério usado.
- **c) Separatrizes:** Q1, Q2 e Q3 (diga qual método de quantil o pandas usa) e a AIQ.
- Extras úteis para o app: P90, P95 e P99 como **limiares de alerta baseados nos dados**.
- Salvar tudo em `saidas/resultados.json`. **O relatório só pode usar números deste arquivo.**
✅ Checkpoint: mostrar a tabela de medidas das duas variáveis.

### Fase 6: Relatório em PDF, Ex. 05 (`06_gerar_relatorio.py`)
Gerar `entrega/relatorio_estatistico_GS_enchentes.pdf` com `reportlab` (ou outra biblioteca
que dê um PDF bem formatado), lendo os números de `resultados.json` e as imagens de `saidas/`.

**Estrutura:**
1. **Capa:** FIAP, Ciência da Computação, disciplina, "Global Solution: CitizenTech",
   título do relatório, integrantes com RM e data.
2. **Sumário executivo** (meia página): o problema, o que foi analisado e os 3 a 5 achados principais.
3. **Contexto e problema:** enchentes em SP, quem é afetado, ligação com o app do grupo e ODS 11 e 13.
4. **Base de dados (Ex. 01):** fonte, estação (com os metadados), período, variáveis e
   **justificativa** (dado oficial, medição horária, estação na capital, ligação direta com alagamento).
5. **Metodologia:** tratamento (faltantes, fuso UTC→local, regra das 20 h, critério de dia chuvoso),
   ferramentas (Python, pandas, matplotlib) e decisões estatísticas.
6. **Resultados**, cada item com **tabela ou gráfico + interpretação em texto**:
   - 6.1 Tabela de frequências: discreta (Ex. 02a)
   - 6.2 Tabela de frequências: contínua (Ex. 02b)
   - 6.3 Gráfico 1: histograma (Ex. 03)
   - 6.4 Gráfico 2: precipitação mensal (Ex. 03)
   - 6.5 Análise univariada 1: volume diário (Ex. 04)
   - 6.6 Análise univariada 2: intensidade horária (Ex. 04)
   Interprete de verdade: assimetria (média vs. mediana), o que o CV alto quer dizer,
   o que significa estar acima do Q3 ou do P95, concentração sazonal etc.
7. **Insights para a solução:** propor limiares de alerta (ex.: P90 e P95 de `pico_mm_h`),
   meses de maior risco e por que a intensidade horária é melhor gatilho que o volume diário.
   Tudo apoiado nos números calculados.
8. **Limitações:** uma estação só (mede a cidade, não cada rua), 2026 parcial, só 2 anos
   de série, a análise não liga a chuva aos pontos de alagamento (sugerir dados do CGE como
   próximo passo) e análise só univariada.
9. **Conclusão.**
10. **Referências:** INMET (com o link), documentação do pandas e do matplotlib, e as fontes
    de qualquer critério citado (ex.: classificação do CV).

**Regras do relatório:**
- Português formal e técnico, numeração em tabelas e figuras ("Tabela 1", "Figura 1"),
  com fonte embaixo de cada uma.
- Números com vírgula decimal e 2 casas, sempre com unidade (mm, mm/h, h, dias).
- **Não invente nenhum número, limiar oficial ou classificação sem fonte.**
  Se for citar classes de intensidade de chuva da Defesa Civil, CGE ou INMET, busque e cite a fonte.
  Se não der, use só os percentis dos dados.
- Nome e RM dos integrantes na capa e no rodapé de todas as páginas.
✅ Checkpoint: abrir o PDF, conferir página por página e listar o que pode melhorar.

### Fase 7: Pacote de entrega
Em `entrega/` deve ficar **só**:
- `base_chuvas_A701_2025_2026.xlsx`
- os `.py` de `src/` (copiados, com cabeçalho de integrantes)
- `relatorio_estatistico_GS_enchentes.pdf`

---

## 6. Checklist final (cada item faltando = −1,0 ponto)

Antes de dizer que terminou, confira item por item e mostre o resultado:

- [ ] Nome completo + RM de todos os integrantes **em todos os arquivos** (xlsx, cada .py, PDF)
- [ ] Base real, com fonte e justificativa no relatório (Ex. 01)
- [ ] Tabela de frequência de variável **discreta** (Ex. 02a)
- [ ] Tabela de frequência de variável **contínua**, com classes justificadas (Ex. 02b)
- [ ] 2 gráficos de **tipos diferentes** e **variáveis diferentes** (Ex. 03)
- [ ] Os gráficos têm título, rótulos de x e y, cor, legenda/fonte (Ex. 03)
- [ ] 2 análises univariadas (Ex. 04)
- [ ] Em cada uma: média, mediana, moda (04a)
- [ ] Em cada uma: máx, mín, amplitude, variância, desvio padrão, CV (04b)
- [ ] Em cada uma: quartis (04c)
- [ ] Interpretação escrita para cada tabela, gráfico e medida (Ex. 05)
- [ ] Insights ligados ao problema de enchentes (Ex. 05)
- [ ] Base em .xlsx/.csv, códigos em .py, relatório em .pdf (Ex. 06)
- [ ] Nenhum link substituindo arquivo e nenhum dado fictício
- [ ] Todos os scripts rodam do zero sem erro
- [ ] Os números do PDF batem com `resultados.json`

## 7. Como se comportar
- Faça uma fase por vez e pare nos checkpoints.
- Se algo no arquivo real for diferente do esperado aqui (colunas, formato, período), **avise
  e se adapte**. Não force o que está escrito neste arquivo.
- Explique as decisões estatísticas em linguagem simples quando o usuário perguntar.
  Ele precisa conseguir defender o trabalho.
- Não faça commit nem publique nada sem o usuário pedir.
