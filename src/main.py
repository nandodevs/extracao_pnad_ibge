#!/usr/bin/env python3
"""
Ponto de entrada principal para extração de dados das tabelas 4.6 e 4.22
dos PDFs da PNAD (2002-2013).
"""
import os
import sys

# Garante que o diretório raiz do projeto está no path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.core.services.pnad_scraper import PnadScraper
from src.core.services.pnad_processor import PnadProcessor
from src.infrastructure.data_access.excel_writer import ExcelWriter


def main():
    YEAR_START = 2002
    YEAR_END = 2013
    PDF_DIR = os.path.join("data", "pdfs")
    OUTPUT_DIR = os.path.join("data", "spreadsheets")

    print("=" * 60)
    print("EXTRATOR DE DADOS PNAD - TABELAS 4.6 E 4.22")
    print(f"Período: {YEAR_START} a {YEAR_END}")
    print("=" * 60)

    # ----------------------------------------------------------------
    # Etapa 1: Coletar links e baixar PDFs
    # ----------------------------------------------------------------
    print("\n[ETAPA 1] Coletando links e baixando PDFs...")
    scraper = PnadScraper(pdf_dir=PDF_DIR)
    pdfs = scraper.collect_and_download(YEAR_START, YEAR_END)

    if not pdfs:
        print("[FALHA] Nenhum PDF foi baixado. Verifique a conexão e a URL do catálogo.")
        sys.exit(1)

    print(f"[OK] {len(pdfs)} PDFs disponíveis em: {PDF_DIR}")

    # ----------------------------------------------------------------
    # Etapa 2: Processar PDFs e extrair tabelas
    # ----------------------------------------------------------------
    print("\n[ETAPA 2] Processando PDFs e extraindo tabelas 4.6 e 4.22...")
    processor = PnadProcessor(pdf_dir=PDF_DIR)
    data = processor.process_all(pdfs)

    if not data:
        print("[FALHA] Nenhuma tabela foi extraída. Verifique os PDFs e a lógica de extração.")
        sys.exit(1)

    print(f"[OK] Dados extraídos de {len(data)} anos.")

    # ----------------------------------------------------------------
    # Etapa 3: Salvar em .xlsx
    # ----------------------------------------------------------------
    print("\n[ETAPA 3] Salvando dados em arquivo Excel...")
    writer = ExcelWriter(output_dir=OUTPUT_DIR)
    saved = writer.save_all(data)

    if saved:
        print(f"[OK] {len(saved)} arquivo(s) gerado(s) em: {OUTPUT_DIR}")
    else:
        print("[FALHA] Nenhum arquivo foi salvo.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("PROCESSO CONCLUÍDO COM SUCESSO!")
    print("=" * 60)


if __name__ == "__main__":
    main()
