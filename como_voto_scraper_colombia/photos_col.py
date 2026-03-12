from __future__ import annotations

import requests
from pathlib import Path
from .core_col import log, fetch

# Base URLs for legislator photos in Colombia
SENADO_PHOTOS_BASE = "https://www.senado.gov.co/senadores"
CAMARA_PHOTOS_BASE = "https://www.camara.gov.co/representantes"

# Directory to save photos
PHOTOS_DIR = Path("docs/fotos/colombia")
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)


def scrape_legislator_photos_colombia() -> None:
    """Scrape legislator photos from Colombian Senado and Cámara websites."""
    log.info("=== Scraping Colombian legislator photos ===")

    # Example: Hardcoded legislator photo URLs (replace with dynamic scraping logic)
    photo_urls = {
        "senado": [
            "https://www.senado.gov.co/sites/default/files/senador1.jpg",
            "https://www.senado.gov.co/sites/default/files/senador2.jpg",
        ],
        "camara": [
            "https://www.camara.gov.co/sites/default/files/representante1.jpg",
            "https://www.camara.gov.co/sites/default/files/representante2.jpg",
        ],
    }

    for chamber, urls in photo_urls.items():
        for url in urls:
            try:
                log.info(f"Downloading photo: {url}")
                response = fetch(url)
                if response is None:
                    log.warning(f"Failed to download photo: {url}")
                    continue

                # Save photo locally
                photo_name = Path(url).name
                photo_path = PHOTOS_DIR / photo_name
                with open(photo_path, "wb") as f:
                    f.write(response.content)
                log.info(f"Photo saved to {photo_path}")

            except requests.RequestException as e:
                log.error(f"Error downloading photo {url}: {e}")


if __name__ == "__main__":
    scrape_legislator_photos_colombia()