"""
Orquestrador: coleta links e faz download dos PDFs da PNAD.
"""
import os
from typing import List
from src.infrastructure.web.ibge_client import IBGEClient


class PnadScraper:
    """Gerencia a coleta e download dos PDFs da PNAD."""

    def __init__(self, pdf_dir: str = "data/pdfs"):
        self.pdf_dir = pdf_dir
        os.makedirs(self.pdf_dir, exist_ok=True)
        self.client = IBGEClient()

    def collect_and_download(self, year_start: int = 2002, year_end: int = 2013) -> List[str]:
        """
        1) Obtém links dos PDFs no catálogo do IBGE.
        2) Faz download de cada PDF não baixado anteriormente.
        Retorna a lista de caminhos dos PDFs baixados.
        """
        links = self.client.get_pdf_links_from_catalog(year_start, year_end)
        print(f"[INFO] {len(links)} links de PDF encontrados no catálogo.")

        downloaded: List[str] = []
        for url, ano in sorted(links, key=lambda x: x[1]):
            filename = os.path.basename(url.rstrip("/"))
            if not filename.endswith(".pdf"):
                filename = f"pnad_{ano}.pdf"
            save_path = os.path.join(self.pdf_dir, filename)

            if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                print(f"[SKIP] {filename} já existe.")
                downloaded.append(save_path)
                continue

            print(f"[DOWNLOAD] {filename} ...", end=" ")
            success = self.client.download_pdf(url, save_path)
            if success:
                print("OK")
                downloaded.append(save_path)
            else:
                print("FALHOU")

        return downloaded
