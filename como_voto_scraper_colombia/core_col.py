from __future__ import annotations

import logging
import requests
import time
from pathlib import Path

# Base directories for data and logs
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data/colombia"
PHOTOS_DIR = BASE_DIR / "docs/fotos/colombia"

# Rate-limiting: seconds between requests
REQUEST_DELAY = 0.5

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger("scraper_col")

# HTTP session with default headers
SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "ComoVoto-Colombia-Scraper/1.0 (https://github.com/ComoVoto-Colombia; civic project)",
        "Accept-Language": "es-CO,es;q=0.9",
    }
)


def fetch(url: str, delay: float = REQUEST_DELAY, raise_for_status: bool = True) -> requests.Response | None:
    """Fetch a URL with rate limiting and error handling."""
    time.sleep(delay)
    try:
        response = SESSION.get(url, timeout=30)
        if raise_for_status:
            response.raise_for_status()
        return response
    except requests.RequestException as exc:
        log.warning(f"Failed to fetch {url}: {exc}")
        return None


def ensure_dirs() -> None:
    """Ensure that all necessary directories exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    log.info("Data and photo directories ensured.")


if __name__ == "__main__":
    ensure_dirs()