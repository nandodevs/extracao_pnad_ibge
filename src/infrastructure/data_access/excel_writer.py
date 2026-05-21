"""
Escrita de dados extraídos em arquivos .xlsx.
"""
import os
import pandas as pd
from typing import Dict, List


class ExcelWriter:
    """Salva DataFrames em arquivos Excel."""

    def __init__(self, output_dir: str = "data/spreadsheets"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def save_all(self, all_data: Dict[int, Dict[str, pd.DataFrame]]) -> List[str]:
        """
        all_data: { ano: { "tabela_4_6": DataFrame, "tabela_4_22": DataFrame } }
        Cria um único arquivo .xlsx com abas separadas por ano e tabela.
        Retorna lista de arquivos salvos.
        """
        filepath = os.path.join(self.output_dir, "pnad_tabelas_4_6_e_4_22.xlsx")
        saved_files: List[str] = []

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            for ano in sorted(all_data.keys()):
                for nome_tabela in ("tabela_4_6", "tabela_4_22"):
                    if nome_tabela in all_data[ano]:
                        df = all_data[ano][nome_tabela]
                        sheet_name = f"{ano}_{nome_tabela}"[:31]  # max 31 chars
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

        if os.path.exists(filepath):
            print(f"[XLSX] Arquivo consolidado salvo: {filepath}")
            saved_files.append(filepath)

        # Opcional: também salva arquivos individuais por ano
        for ano in sorted(all_data.keys()):
            for nome_tabela in ("tabela_4_6", "tabela_4_22"):
                if nome_tabela in all_data[ano]:
                    df = all_data[ano][nome_tabela]
                    ano_file = os.path.join(
                        self.output_dir, f"pnad_{ano}_{nome_tabela}.xlsx"
                    )
                    df.to_excel(ano_file, index=False)
                    saved_files.append(ano_file)

        return saved_files
