"""
Cliente HTTP para interagir com o site do IBGE e obter links de PDFs.
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Tuple
from urllib.parse import urljoin


class IBGEClient:
    """Cliente para capturar links de PDFs da PNAD no catálogo do IBGE."""

    CATALOG_URL = "https://biblioteca.ibge.gov.br/index.php/biblioteca-catalogo?view=detalhes&id=759"
    INDEX_URL = "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_anual/2015/Volume_Brasil/Brasil/00_indice_tabelas_brasil.txt"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        })

    def get_pdf_links_from_catalog(self, year_start: int = 2002, year_end: int = 2013) -> List[Tuple[str, int]]:
        """
        Acessa a página do catálogo do IBGE e extrai os links dos PDFs
        para os anos entre year_start e year_end.

        Returns:
            Lista de tuplas (url_do_pdf, ano)
        """
        response = self.session.get(self.CATALOG_URL, timeout=self.timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        pdf_links: List[Tuple[str, int]] = []

        # Localiza todas as tags <a> dentro de <td class="col">
        for td in soup.find_all("td", class_="col"):
            link = td.find("a", href=True, title=True)
            if not link:
                continue

            title = link.get("title", "")
            href = link.get("href", "")

            # Ex: "pnad_2002_v23_br.pdf" -> extrai ano 2002
            match = re.search(r"pnad_(\d{4})_v\d+_br\.pdf", title)
            if not match:
                continue

            ano = int(match.group(1))
            if year_start <= ano <= year_end:
                url_abs = urljoin(self.CATALOG_URL, href)
                pdf_links.append((url_abs, ano))

        return pdf_links

    def get_table_index(self) -> str:
        """
        Obtém o conteúdo do arquivo de índice de tabelas.
        """
        response = self.session.get(self.INDEX_URL, timeout=self.timeout)
        response.raise_for_status()
        response.encoding = "utf-8"
        return response.text

    def download_pdf(self, url: str, save_path: str) -> bool:
        """
        Download de um arquivo PDF.
        Retorna True se bem-sucedido.
        """
        try:
            response = self.session.get(url, stream=True, timeout=self.timeout)
            response.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=65536):
                    f.write(chunk)
            return True
        except requests.RequestException as e:
            print(f"[ERRO] Falha ao baixar {url}: {e}")
            return False
