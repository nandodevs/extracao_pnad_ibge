# Extrator de Dados PNAD — Tabelas 4.6 e 4.22

Extrai automaticamente os dados de **Pessoas** e **Rendimento** das tabelas 4.6 e 4.22 dos PDFs da PNAD (Pesquisa Nacional por Amostra de Domicílios) publicados pelo IBGE, abrangendo o período de 2002 a 2013, e os consolida em planilhas `.xlsx`.

## Requisitos Funcionais

- Acessar o catálogo online do IBGE e baixar os PDFs de cada ano automaticamente.
- Localizar as tabelas 4.6 ("Pessoas de 10 anos ou mais de idade, por situação do domicílio e classes de rendimento") e 4.22 ("Pessoas de 10 anos ou mais de idade, por situação do domicílio, classes de rendimento e sexo") dentro de cada PDF.
- Extrair os dados tabulares usando coordenadas espaciais das palavras (preservação de layout), sem depender de OCR.
- Organizar os dados nas colunas: **Ano**, **Situação / Classes de rendimento**, **Pessoas** (Total, Homens, Mulheres), **Rendimento (R$)** (Total, Homens, Mulheres).
- Salvar os resultados em planilhas Excel (um arquivo consolidado com abas por ano/tabela e arquivos individuais).

## Arquitetura

```
project_extract_pnad/
├── src/
│   ├── main.py                           # Ponto de entrada (orquestrador)
│   ├── core/
│   │   ├── services/
│   │   │   ├── pnad_scraper.py           # Orquestra coleta e download dos PDFs
│   │   │   └── pnad_processor.py         # Extrai tabelas via layout espacial (pdfplumber)
│   ├── infrastructure/
│   │   ├── web/
│   │   │   └── ibge_client.py           # Cliente HTTP para catálogo e download do IBGE
│   │   └── data_access/
│   │       └── excel_writer.py          # Persistência em .xlsx (openpyxl + pandas)
│   └── utils/                            # Utilitários (reservado)
├── tests/                                 # Testes unitários
├── data/
│   ├── pdfs/                              # PDFs baixados (2002-2013)
│   └── spreadsheets/                      # Planilhas geradas (.xlsx)
├── .venv/                                 # Ambiente virtual Python
├── requirements.txt
├── README.md
└── context.md
```

## Como Usar

### 1. Ativar o ambiente virtual

```bash
source .venv/bin/activate
```

### 2. Executar o programa

```bash
python src/main.py
```

O programa executa 3 etapas:

1. **Coleta e download** — acessa o catálogo do IBGE e baixa os PDFs não existentes em `data/pdfs/`.
2. **Processamento** — para cada PDF, localiza as tabelas 4.6 e 4.22 e extrai os dados por coordenadas espaciais.
3. **Exportação** — salva os dados extraídos em `data/spreadsheets/pnad_tabelas_4_6_e_4_22.xlsx` (consolidado) e arquivos individuais `pnad_{ano}_{tabela}.xlsx`.

## Dependências

```
requests>=2.31.0
beautifulsoup4>=4.12.0
pandas>=2.1.0
openpyxl>=3.1.0
pdfplumber>=0.10.0
lxml>=5.0.0
html5lib>=1.1
```

Instale com:

```bash
pip install -r requirements.txt
```

## Resultados

| Anos processados | Tabela 4.6 | Tabela 4.22 |
|-----------------|------------|-------------|
| 2002            | OK         | OK          |
| 2003            | **FALHA**  | **FALHA**   |
| 2004            | OK         | OK          |
| 2005            | OK         | OK          |
| 2006            | OK         | OK          |
| 2007            | OK         | OK          |
| 2008            | OK         | OK          |
| 2009            | OK         | OK          |
| 2011            | OK         | OK          |
| 2012            | OK         | OK          |
| 2013            | OK         | OK          |

**Total: 10 anos processados com sucesso** (2002, 2004–2013).

> O ano de 2010 não é contemplado pois a PNAD não foi a campo — ano do Censo Demográfico.

## Limitação Conhecida

**PDF de 2003**: O arquivo `pnad_2003_v23_br.pdf` utiliza uma **codificação proprietária de fonte** (CJK / fonte embedada não padrão) que impede a extração automática do texto por bibliotecas como `pdfplumber`. Isso faz com que as páginas retornem texto vazio, inviabilizando a localização e extração das tabelas 4.6 e 4.22 para este ano. Uma abordagem alternativa seria utilizar OCR (ex.: `pytesseract` + `pdf2image`) para processar este PDF específico.

## Formato dos Dados

As planilhas geradas seguem a estrutura:

| Coluna                      | Descrição                                          |
|-----------------------------|----------------------------------------------------|
| Ano                         | Ano da pesquisa (ex.: 2002, 2004...)               |
| Situação / Classes de rendimento | Descrição da linha (ex.: "Total", "Urbana", "Até 1/2 salário mínimo") |
| Pessoas - Total             | Total de pessoas na categoria                      |
| Pessoas - Homens            | Homens na categoria                                |
| Pessoas - Mulheres          | Mulheres na categoria                              |
| Rendimento (R$) - Total     | Rendimento médio (R$) — Total                      |
| Rendimento (R$) - Homens    | Rendimento médio (R$) — Homens                     |
| Rendimento (R$) - Mulheres  | Rendimento médio (R$) — Mulheres                   |

**Observação**: Os valores numéricos podem conter **espaço como separador de milhar** (ex.: `1 234`) conforme publicado pelo IBGE. Recomenda-se tratar esse formato ao realizar análises quantitativas (substituir espaço por vazio e converter para numérico).
