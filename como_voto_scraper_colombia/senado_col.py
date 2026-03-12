from __future__ import annotations

import requests
import pandas as pd
from pathlib import Path
from .core_col import log, fetch

# Base URL for Senado data in Colombia
SENADO_BASE = "https://www.datos.gov.co/resource/ucmr-52df.json"

# Directory to save processed data
DATA_DIR = Path("data/colombia")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def scrape_senado_colombia() -> None:
    """Scrape voting data from the Colombian Senado API."""
    log.info("=== Scraping Colombian Senado data ===")

    # Fetch data from the API
    try:
        response = fetch(SENADO_BASE)
        if response is None:
            log.error("Failed to fetch Senado data.")
            return

        # Parse JSON response
        data = response.json()
        df = pd.DataFrame(data)

        # Save raw data to a CSV file
        raw_csv_path = DATA_DIR / "senado_raw.csv"
        df.to_csv(raw_csv_path, index=False, encoding="utf-8")
        log.info(f"Raw Senado data saved to {raw_csv_path}")

        # Process and normalize data (example: filter columns, rename headers)
        processed_df = df[["fecha", "proyecto", "resultado", "afirmativos", "negativos", "abstenciones"]]
        processed_df.columns = ["date", "law", "result", "affirmative", "negative", "abstention"]

        # Save processed data to a JSON file
        processed_json_path = DATA_DIR / "senado_processed.json"
        processed_df.to_json(processed_json_path, orient="records", force_ascii=False, indent=2)
        log.info(f"Processed Senado data saved to {processed_json_path}")

    except requests.RequestException as e:
        log.error(f"Error fetching Senado data: {e}")


if __name__ == "__main__":
    scrape_senado_colombia()