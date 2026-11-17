# -*- coding: utf-8 -*-
"""
=============================================================================
Disciplina : Modelagem Linear e Aprendizado de Máquina — Ciência da Computação (1º semestre) — FIAP
Trabalho   : Global Solution CitizenTech — Enchentes e alagamentos em São Paulo
Integrantes:
    Fernando Campos Garnica Mota  — RM 567451
    André da Silva Pinto          — RM 559038
-----------------------------------------------------------------------------
Script 01 — Download e extração dos dados
    Baixa os arquivos anuais de Dados Históricos do INMET (2025 e 2026),
    extrai SOMENTE o CSV da estação automática A701 (São Paulo - Mirante
    de Santana) e imprime os metadados da estação e as primeiras linhas.
    Os arquivos originais ficam em dados/brutos/ e não são alterados.
=============================================================================
"""
import sys
import zipfile
from pathlib import Path

import requests
import truststore

# Usa os certificados confiáveis do sistema operacional (Windows) para validar
# o HTTPS do INMET. A verificação continua ligada; só muda a lista de autoridades.
truststore.inject_into_ssl()

# Garante que acentos apareçam no terminal do Windows sem erro.
for _fluxo in (sys.stdout, sys.stderr):
    if hasattr(_fluxo, "reconfigure"):
        _fluxo.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
PASTA_BRUTOS = RAIZ / "dados" / "brutos"
ANOS = [2025, 2026]
URL_BASE = "https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip"
CODIGO_ESTACAO = "A701"
# O servidor do INMET recusa clientes sem User-Agent de navegador.
CABECALHOS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
ENCODING_INMET = "latin-1"
LINHAS_METADADOS = 8


def baixar_zip(ano: int) -> Path:
    """Baixa o ZIP do ano, pulando se já existir em dados/brutos/."""
    destino = PASTA_BRUTOS / f"{ano}.zip"
    if destino.exists() and zipfile.is_zipfile(destino):
        print(f"[{ano}] ZIP já existe ({destino.stat().st_size / 1e6:.1f} MB), pulando download.")
        return destino

    url = URL_BASE.format(ano=ano)
    print(f"[{ano}] Baixando {url} ...")
    temporario = destino.with_suffix(".zip.part")
    try:
        with requests.get(url, headers=CABECALHOS, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            with open(temporario, "wb") as arq:
                for bloco in resp.iter_content(chunk_size=1 << 20):
                    arq.write(bloco)
    except requests.RequestException as erro:
        temporario.unlink(missing_ok=True)
        sys.exit(
            f"\nFalha no download de {url}: {erro}\n"
            f"Baixe o arquivo manualmente e coloque em {PASTA_BRUTOS}. "
            "Nenhum dado será inventado ou simulado."
        )
    temporario.replace(destino)
    print(f"[{ano}] Download concluído ({destino.stat().st_size / 1e6:.1f} MB).")
    return destino


def extrair_a701(caminho_zip: Path) -> Path:
    """Extrai apenas o CSV cujo nome contém o código da estação A701."""
    with zipfile.ZipFile(caminho_zip) as zf:
        candidatos = [n for n in zf.namelist()
                      if CODIGO_ESTACAO in Path(n).name.upper() and n.lower().endswith(".csv")]
        if len(candidatos) != 1:
            sys.exit(f"Esperado 1 CSV da {CODIGO_ESTACAO} em {caminho_zip.name}, encontrados: {candidatos}")
        nome_interno = candidatos[0]
        destino = PASTA_BRUTOS / Path(nome_interno).name
        if not destino.exists():
            with zf.open(nome_interno) as origem, open(destino, "wb") as saida:
                saida.write(origem.read())
        return destino


def inspecionar_csv(caminho_csv: Path) -> None:
    """Mostra metadados, colunas, primeiras linhas e primeira/última data."""
    with open(caminho_csv, encoding=ENCODING_INMET) as arq:
        linhas = arq.read().splitlines()

    print(f"\nArquivo: {caminho_csv.name}")
    print("Metadados da estação:")
    for linha in linhas[:LINHAS_METADADOS]:
        print("   ", linha)

    cabecalho = linhas[LINHAS_METADADOS].split(";")
    print(f"Colunas ({len([c for c in cabecalho if c])}):")
    for i, col in enumerate(cabecalho):
        if col:
            print(f"    {i:2d}. {col}")

    dados = [l for l in linhas[LINHAS_METADADOS + 1:] if l.strip()]
    print("Primeiras 3 linhas de dados:")
    for linha in dados[:3]:
        print("   ", linha)
    print(f"Linhas de dados: {len(dados)}")
    print(f"Primeira data/hora: {dados[0].split(';')[0]} {dados[0].split(';')[1]}")
    print(f"Última data/hora  : {dados[-1].split(';')[0]} {dados[-1].split(';')[1]}")


def main() -> None:
    PASTA_BRUTOS.mkdir(parents=True, exist_ok=True)
    for ano in ANOS:
        caminho_zip = baixar_zip(ano)
        caminho_csv = extrair_a701(caminho_zip)
        inspecionar_csv(caminho_csv)
        print("-" * 78)


if __name__ == "__main__":
    main()
