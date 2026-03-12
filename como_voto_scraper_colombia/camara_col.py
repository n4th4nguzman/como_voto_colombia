from __future__ import annotations

import requests
import pdfplumber
from pathlib import Path
from .core_col import log, fetch

# Base URL for Cámara de Representantes data in Colombia
CAMARA_BASE = "https://www.camara.gov.co/secretaria-general/actas-votaciones-y-otros/"

# Directory to save processed data
DATA_DIR = Path("data/colombia")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def scrape_camara_colombia() -> None:
    """Scrape voting data from the Colombian Cámara de Representantes."""
    log.info("=== Scraping Colombian Cámara de Representantes data ===")

    # Fetch the list of PDFs (manual or automated discovery)
    try:
        response = fetch(CAMARA_BASE)
        if response is None:
            log.error("Failed to fetch Cámara de Representantes data.")
            return

        # Example: Parse the HTML to find PDF links (simplified)
        pdf_links = [
            "https://www.camara.gov.co/sites/default/files/acta_votacion_1.pdf",
            "https://www.camara.gov.co/sites/default/files/acta_votacion_2.pdf",
        ]

        all_votes = []

        for pdf_url in pdf_links:
            log.info(f"Processing PDF: {pdf_url}")
            pdf_response = fetch(pdf_url)
            if pdf_response is None:
                log.warning(f"Failed to download PDF: {pdf_url}")
                continue

            # Save the PDF locally
            pdf_path = DATA_DIR / Path(pdf_url).name
            with open(pdf_path, "wb") as f:
                f.write(pdf_response.content)

            # Extract tables from the PDF
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        all_votes.extend(table)

        # Process and normalize data (example: convert to DataFrame)
        # Assuming the table structure is consistent
        import pandas as pd

        df = pd.DataFrame(all_votes, columns=["legislator", "vote", "law", "date"])
        processed_csv_path = DATA_DIR / "camara_processed.csv"
        df.to_csv(processed_csv_path, index=False, encoding="utf-8")
        log.info(f"Processed Cámara data saved to {processed_csv_path}")

    except requests.RequestException as e:
        log.error(f"Error fetching Cámara data: {e}")


if __name__ == "__main__":
    scrape_camara_colombia()