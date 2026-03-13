from __future__ import annotations

import json
import re
import time
import unicodedata
from pathlib import Path

from bs4 import BeautifulSoup

from .core_col import BASE_DIR, REQUEST_DELAY, SESSION, log

# Photo map JSONs live in data/ (not data/colombia/) — matches data_loading.load_photo_maps()
_DATA_DIR = BASE_DIR / "data"
# Photos are stored under docs/fotos/colombia/ and referenced as "fotos/colombia/<file>"
PHOTOS_DIR = BASE_DIR / "docs" / "fotos" / "colombia"

SENADO_LIST_URL = "https://www.senado.gov.co/index.php/el-senado/senadores"
CAMARA_LIST_URL = "https://www.camara.gov.co/representantes"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug(name: str) -> str:
    """Convert a display name to a safe ASCII filename stem."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Za-z0-9]+", "_", ascii_str).strip("_").lower()


def _download_image(url: str, dest: Path) -> bool:
    """Download an image URL to dest; returns True on success."""
    if dest.exists():
        return True  # already cached
    time.sleep(REQUEST_DELAY)
    try:
        r = SESSION.get(url, timeout=30)
        r.raise_for_status()
        content_type = r.headers.get("content-type", "")
        if "image" not in content_type and len(r.content) < 500:
            log.debug(f"Skipping non-image response for {url}")
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)
        return True
    except Exception as exc:
        log.warning(f"Failed to download {url}: {exc}")
        return False


def _save_photo_map(path: Path, mapping: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(mapping, fh, ensure_ascii=False, indent=2)
    log.info(f"Saved photo map: {path} ({len(mapping)} entries)")


# ---------------------------------------------------------------------------
# Senado scraper
# ---------------------------------------------------------------------------

def scrape_senado_photos() -> dict[str, str]:
    """Scrape senator headshots from senado.gov.co.

    Returns a mapping of {display_name: colombia/<filename>} ready to be saved
    to data/senadores_col_photos.json.
    """
    log.info("Fetching senator list from senado.gov.co...")
    try:
        r = SESSION.get(SENADO_LIST_URL, timeout=20)
        r.raise_for_status()
    except Exception as exc:
        log.error(f"Could not fetch Senado senators page: {exc}")
        return {}

    soup = BeautifulSoup(r.text, "lxml")

    # Each senator headshot has src containing /Fotos_Senadores or /images/Senadores
    # and an alt attribute with the name in "Apellido Nombre" form.
    seen: set[str] = set()
    photo_map: dict[str, str] = {}

    for img in soup.find_all("img", src=True):
        src: str = img.get("src", "")
        alt: str = img.get("alt", "").strip()
        if not alt:
            continue
        if not any(kw in src for kw in ("Fotos_Senadores", "/images/Senadores")):
            continue
        if alt in seen:
            continue
        seen.add(alt)

        # Ensure absolute URL
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            src = "https://www.senado.gov.co" + src

        # Determine file extension from URL
        url_path = src.split("?")[0]
        ext = Path(url_path).suffix.lower() or ".jpg"
        filename = f"sen_col_{_slug(alt)}{ext}"
        dest = PHOTOS_DIR / filename

        log.info(f"  Senator: {alt!r} -> {filename}")
        if _download_image(src, dest):
            photo_map[alt] = f"colombia/{filename}"
        else:
            log.warning(f"  Could not download photo for {alt!r}")

    log.info(f"Scraped {len(photo_map)} senator photos")
    return photo_map


# ---------------------------------------------------------------------------
# Cámara scraper
# ---------------------------------------------------------------------------

def _extract_camara_reps(html: str) -> list[dict]:
    """Extract {Nombre, Imagen} pairs from the departamentosInfo JS object."""
    # The page embeds: const departamentosInfo={"DEPTO":[{...},...],...}
    m = re.search(r"const\s+departamentosInfo\s*=\s*(\{.*?\});", html, re.DOTALL)
    if not m:
        log.warning("departamentosInfo not found in Cámara page")
        return []
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        log.warning(f"Could not parse departamentosInfo: {exc}")
        return []

    reps: list[dict] = []
    for dept_list in data.values():
        if isinstance(dept_list, list):
            reps.extend(dept_list)
    return reps


def scrape_camara_photos() -> dict[str, str]:
    """Scrape representative headshots from camara.gov.co.

    Returns a mapping of {display_name: colombia/<filename>}.
    """
    log.info("Fetching representatives list from camara.gov.co...")
    try:
        r = SESSION.get(CAMARA_LIST_URL, timeout=20)
        r.raise_for_status()
    except Exception as exc:
        log.error(f"Could not fetch Cámara representantes page: {exc}")
        return {}

    reps = _extract_camara_reps(r.text)
    log.info(f"Found {len(reps)} representatives in departamentosInfo")

    photo_map: dict[str, str] = {}
    for rep in reps:
        name: str = rep.get("Nombre", "").strip()
        img_url: str = rep.get("Imagen", "").strip()
        if not name or not img_url:
            continue

        url_path = img_url.split("?")[0]
        ext = Path(url_path).suffix.lower() or ".jpg"
        filename = f"rep_col_{_slug(name)}{ext}"
        dest = PHOTOS_DIR / filename

        log.info(f"  Rep: {name!r} -> {filename}")
        if _download_image(img_url, dest):
            photo_map[name] = f"colombia/{filename}"
        else:
            log.warning(f"  Could not download photo for {name!r}")

    log.info(f"Scraped {len(photo_map)} representative photos")
    return photo_map


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def scrape_legislator_photos_colombia() -> None:
    """Scrape and save Colombian legislator photos for both chambers."""
    log.info("=== Scraping Colombian legislator photos ===")
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

    senator_map = scrape_senado_photos()
    _save_photo_map(_DATA_DIR / "senadores_col_photos.json", senator_map)

    rep_map = scrape_camara_photos()
    _save_photo_map(_DATA_DIR / "representantes_photos.json", rep_map)

    log.info(
        f"=== Photo scrape complete: "
        f"{len(senator_map)} senators, {len(rep_map)} representatives ==="
    )


if __name__ == "__main__":
    scrape_legislator_photos_colombia()