"""
Processador de PDFs: extrai tabelas 4.6 e 4.22 usando coordenadas
espaciais das palavras no PDF (layout preservation).
"""
import os
import re
import math
import pandas as pd
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class PnadProcessor:
    """Extrai tabelas 4.6 e 4.22 de PDFs da PNAD usando layout espacial."""

    # Margens esperadas para as colunas de dados (valores empíricos)
    # Estas podem variar entre anos, mas servem como heurística inicial

    def __init__(self, pdf_dir: str = "data/pdfs"):
        self.pdf_dir = pdf_dir

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def process_pdf(self, pdf_path: str) -> Dict[str, pd.DataFrame]:
        filename = os.path.basename(pdf_path)
        ano = self._extract_year(filename)
        print(f"[PROCESS] {filename} (ano {ano})")

        result: Dict[str, pd.DataFrame] = {}

        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for table_id, key in [("4.6", "tabela_4_6"), ("4.22", "tabela_4_22")]:
                pages_info = self._find_table_pages(pdf, table_id)
                if not pages_info:
                    continue
                df = self._extract_table_from_words(
                    pdf, pages_info, table_id, ano
                )
                if df is not None and not df.empty:
                    result[key] = df
                    print(f"  [OK] Tabela {table_id} ({len(df)} linhas)")

        if not result:
            print(f"  [AVISO] Nenhuma tabela encontrada em {filename}")

        return result

    def process_all(self, pdf_paths: List[str]) -> Dict[int, Dict[str, pd.DataFrame]]:
        all_data: Dict[int, Dict[str, pd.DataFrame]] = {}
        for pdf_path in sorted(pdf_paths):
            ano = self._extract_year(os.path.basename(pdf_path))
            if ano is None:
                continue
            tables = self.process_pdf(pdf_path)
            if tables:
                all_data[ano] = tables
        return all_data

    # ------------------------------------------------------------------
    # Localização das páginas das tabelas
    # ------------------------------------------------------------------
    @staticmethod
    def _find_table_pages(pdf, table_id: str) -> Optional[List[int]]:
        """
        Retorna a lista de números de página (0-indexed) onde a tabela
        aparece. Procura pelo texto "Tabela X.Y" no conteúdo das páginas.
        """
        result_pages = []
        found_start = False

        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            # Início da tabela
            if re.search(rf"Tabela\s+{re.escape(table_id)}\b", text, re.IGNORECASE):
                found_start = True
                result_pages.append(page_num)
                continue
            # Continua capturando páginas enquanto forem dados da mesma tabela
            # (páginas sem "Tabela X.Y" na sequência)
            if found_start:
                if re.search(r"\bTabela\s+\d+\.\d+\b", text, re.IGNORECASE):
                    # É outra tabela, para
                    break
                result_pages.append(page_num)

        return result_pages if result_pages else None

    # ------------------------------------------------------------------
    # Extração tabular usando coordenadas
    # ------------------------------------------------------------------
    def _extract_table_from_words(
        self, pdf, page_nums: List[int], table_id: str, ano: Optional[int]
    ) -> Optional[pd.DataFrame]:
        """
        Extrai a tabela identificando colunas pela posição X das palavras.
        """
        # Coleta todas as palavras (com coordenadas) das páginas da tabela
        all_words = []  # (text, x0, x1, y0, page_num)
        for page_num in page_nums:
            page = pdf.pages[page_num]
            words = page.extract_words(keep_blank_chars=True, x_tolerance=1)
            # Filtra cabeçalho "4 - Trabalho" que aparece em todas as páginas
            for w in words:
                text = w["text"].strip()
                if not text:
                    continue
                # Pula o cabeçalho de página "4 - Trabalho"
                if re.match(r"^\d\s*-\s*Trabalho$", text):
                    continue
                all_words.append({
                    "text": text,
                    "x0": w["x0"],
                    "x1": w["x1"],
                    "y0": w["top"],
                    "page": page_num,
                })

        if not all_words:
            return None

        # Agrupa palavras na mesma linha (mesmo y)
        lines = self._group_words_into_lines(all_words)

        # Encontra a linha de cabeçalho da tabela
        header_idx = None
        for i, line in enumerate(lines):
            texts = [w["text"] for w in line]
            line_str = " ".join(texts)
            if self._is_col_header(line_str):
                header_idx = i
                break

        if header_idx is None:
            return None

        # Extrai cabeçalho e linhas de dados
        header_words = lines[header_idx]
        col_boundaries = self._determine_column_boundaries(header_words)

        # Gera nomes de colunas baseado no cabeçalho
        col_names = self._make_col_names(col_boundaries)

        # Processa linhas de dados
        data_rows = []
        for i in range(header_idx + 1, len(lines)):
            line = lines[i]
            texts = [w["text"] for w in line]
            line_str = " ".join(texts)

            # Verifica fim da tabela
            if re.search(r"\b(Tabela\s+|Fonte:|Nota:|Tabelas de resultados)", line_str):
                break

            row = self._assign_words_to_columns(line, col_boundaries, header_words)
            if row:
                data_rows.append(row)

        if not data_rows:
            return None

        # Converte para DataFrame
        df = pd.DataFrame(data_rows, columns=["Situação / Classes de rendimento"] + col_names)
        if ano is not None:
            df.insert(0, "Ano", ano)

        return df

    # ------------------------------------------------------------------
    # Métodos auxiliares
    # ------------------------------------------------------------------
    @staticmethod
    def _group_words_into_lines(words: List[dict], y_tolerance: float = 3) -> List[List[dict]]:
        """Agrupa palavras que estão na mesma linha (mesmo y com tolerância)."""
        sorted_words = sorted(words, key=lambda w: (w["y0"], w["x0"]))
        lines = []
        current_line = []
        current_y = None

        for w in sorted_words:
            if current_y is None or abs(w["y0"] - current_y) > y_tolerance:
                if current_line:
                    lines.append(current_line)
                current_line = [w]
                current_y = w["y0"]
            else:
                current_line.append(w)

        if current_line:
            lines.append(current_line)

        return lines

    @staticmethod
    def _is_col_header(line_str: str) -> bool:
        """Identifica linha de cabeçalho."""
        return bool(re.search(r"\bTotal\b", line_str) and re.search(r"\bHomens\b", line_str) and re.search(r"\bMulheres\b", line_str))

    def _determine_column_boundaries(self, header_words: List[dict]) -> List[Tuple[float, float, str]]:
        """
        Determina os limites X de cada coluna baseado na posição das
        palavras do cabeçalho.
        Retorna lista de (x0, x1, nome_coluna).
        """
        # Mapa de palavras do cabeçalho para eixos X
        # Ordena por x0
        sorted_h = sorted(header_words, key=lambda w: w["x0"])

        boundaries = []
        for w in sorted_h:
            boundaries.append((w["x0"], w["x1"], w["text"]))

        # Expande os limites para incluir gaps entre colunas
        expanded = []
        for i, (x0, x1, text) in enumerate(boundaries):
            if i < len(boundaries) - 1:
                next_x0 = boundaries[i + 1][0]
                # O limite direito é o ponto médio entre esta palavra e a próxima
                right = (x1 + next_x0) / 2
            else:
                right = x1 + 20  # margem para a última coluna

            if i > 0:
                prev_x1 = boundaries[i - 1][1]
                left = (prev_x1 + x0) / 2
            else:
                left = max(0, x0 - 20)

            expanded.append((left, right, text))

        return expanded

    @staticmethod
    def _make_col_names(boundaries: List[Tuple[float, float, str]]) -> List[str]:
        """
        Converte as palavras do cabeçalho em nomes de coluna.
        Ex: ["Total", "Homens", "Mulheres", "Total", "Homens", "Mulheres"]
            -> ["Pessoas - Total", "Pessoas - Homens", "Pessoas - Mulheres",
                "Rendimento (R$) - Total", "Rendimento (R$) - Homens", "Rendimento (R$) - Mulheres"]
        """
        raw = [b[2] for b in boundaries]
        n = len(raw)
        names = []
        # Agrupa em duas metades: pessoas e rendimento
        half = n // 2
        for i, name in enumerate(raw):
            if i < half:
                prefix = "Pessoas"
            else:
                prefix = "Rendimento (R$)"
            names.append(f"{prefix} - {name}")
        return names

    def _assign_words_to_columns(
        self, line_words: List[dict],
        col_boundaries: List[Tuple[float, float, str]],
        header_words: List[dict],
    ) -> Optional[List[str]]:
        """
        Atribui cada palavra da linha à coluna correta baseado na posição X.
        Retorna [label, val1, val2, ..., valN].
        """
        # Se não há palavras, retorna None
        if not line_words:
            return None

        n_cols = len(col_boundaries)
        values = [""] * n_cols
        label_parts = []

        for w in sorted(line_words, key=lambda x: x["x0"]):
            x0 = w["x0"]
            text = w["text"]
            assigned = False

            for i, (left, right, _) in enumerate(col_boundaries):
                if left <= x0 <= right:
                    if values[i]:
                        values[i] += " " + text
                    else:
                        values[i] = text
                    assigned = True
                    break

            if not assigned:
                # Palavra fora das colunas -> parte do label
                label_parts.append(text)

        # Se todas as colunas estão vazias, é uma linha de label
        if all(v == "" for v in values):
            return None

        label = " ".join(label_parts) if label_parts else ""
        return [label] + values

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_year(filename: str) -> Optional[int]:
        m = re.search(r"(\d{4})", filename)
        return int(m.group(1)) if m else None
