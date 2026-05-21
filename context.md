# Contexto do Projeto — Extrator PNAD

## Estrutura do Projeto

```
project_extract_pnad/
├── src/
│   ├── main.py                         # Orquestrador: download → processamento → exportação
│   ├── core/
│   │   └── services/
│   │       ├── pnad_scraper.py         # Gerencia coleta de links + download dos PDFs
│   │       └── pnad_processor.py       # Extração tabular por layout espacial (pdfplumber)
│   ├── infrastructure/
│   │   ├── web/
│   │   │   └── ibge_client.py         # HTTP client para catálogo e FTP do IBGE
│   │   └── data_access/
│   │       └── excel_writer.py         # Persistência em Excel (pandas + openpyxl)
│   └── utils/                          # Utilitários (reservado)
├── tests/                              # Testes unitários (esqueleto)
├── data/
│   ├── pdfs/                           # PDFs baixados por ano (2002-2013)
│   └── spreadsheets/                   # Planilhas .xlsx geradas
├── .venv/                              # Ambiente virtual Python 3.12
├── requirements.txt
├── README.md
└── context.md
```

## Agentes e Responsabilidades

| Agente | Responsabilidade |
|--------|-----------------|
| **IBGEClient** | Acessa o catálogo online do IBGE, extrai links dos PDFs e faz download. |
| **PnadScraper** | Orquestra a etapa de coleta: usa IBGEClient para obter links e baixar arquivos. |
| **PnadProcessor** | Abre cada PDF com pdfplumber, localiza páginas das tabelas 4.6/4.22 por regex, extrai linhas por coordenadas X/Y das palavras e monta DataFrames. |
| **ExcelWriter** | Recebe os dicionários de DataFrames e persiste em arquivos `.xlsx` (consolidado + individuais). |
| **main.py** | Orquestrador final: executa as 3 etapas em sequência. |

## Status Final do Projeto

- **Período**: 2002 a 2013 (exceto 2010 — ano de Censo, sem PNAD).
- **10 anos processados com sucesso**: 2002, 2004, 2005, 2006, 2007, 2008, 2009, 2011, 2012, 2013.
- **2003 — falha documentada**: PDF com codificação proprietária de fonte impossibilita extração de texto por pdfplumber.
- **PDFs baixados**: 11 anos (v23 e v24/vXX por ano).
- **Planilhas geradas**: 1 arquivo consolidado + 20 arquivos individuais (2 tabelas × 10 anos).
- **Código funcional e testado** em Python 3.12.

## Fluxo de Trabalho

```
main()
  ├── [Etapa 1] PnadScraper.collect_and_download()
  │     └── IBGEClient.get_pdf_links_from_catalog()
  │     └── IBGEClient.download_pdf()
  ├── [Etapa 2] PnadProcessor.process_all()
  │     └── PnadProcessor.process_pdf()
  │           ├── _find_table_pages()              # Localiza páginas das tabelas
  │           └── _extract_table_from_words()       # Extrai por coordenadas
  │                 ├── _group_words_into_lines()
  │                 ├── _is_col_header()
  │                 ├── _determine_column_boundaries()
  │                 ├── _make_col_names()
  │                 └── _assign_words_to_columns()
  └── [Etapa 3] ExcelWriter.save_all()
        └── pd.ExcelWriter() + df.to_excel()
```
