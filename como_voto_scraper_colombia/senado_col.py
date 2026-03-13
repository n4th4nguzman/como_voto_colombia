from __future__ import annotations

import hashlib
import re
import time
import unicodedata
import urllib.parse
from collections import defaultdict
from datetime import datetime

from pathlib import Path as _Path
from .core_col import REQUEST_DELAY, SESSION, log

# ConsolidatedDB files live in data/ root (not data/colombia/)
_DB_DIR = _Path(__file__).resolve().parent.parent / "data"
_DB_DIR.mkdir(parents=True, exist_ok=True)

try:
    from como_voto_scraper.db import ConsolidatedDB
except ImportError:
    from scraper import ConsolidatedDB  # type: ignore

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------
SODA_BASE = "https://www.datos.gov.co/resource"
VOTES_DATASET = "ucmr-52df"     # Individual senator votes: fecha, fullname, proyecto, vote
SENATORS_DATASET = "sjwx-dr6n"  # Senator roster with party info (2018-2022)

PAGE_SIZE = 10_000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_soda(dataset_id: str, offset: int = 0, limit: int = PAGE_SIZE, **kwargs) -> list[dict]:
    """Fetch one page from a Socrata SODA dataset."""
    params: dict = {"$limit": limit, "$offset": offset}
    for k, v in kwargs.items():
        params[f"${k}"] = v
    url = f"{SODA_BASE}/{dataset_id}.json"
    time.sleep(REQUEST_DELAY)
    try:
        r = SESSION.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        log.warning(f"SODA fetch error ({dataset_id}): {exc}")
        return []


def _fetch_all_soda(dataset_id: str, **kwargs) -> list[dict]:
    """Collect all records from a SODA dataset with automatic pagination."""
    records: list[dict] = []
    offset = 0
    while True:
        page = _fetch_soda(dataset_id, offset=offset, **kwargs)
        if not page:
            break
        records.extend(page)
        log.info(f"  {dataset_id}: {len(records)} records...")
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return records


def _norm_key(name: str) -> str:
    """Uppercase ASCII without spaces — used to match names across sources."""
    nfkd = unicodedata.normalize("NFKD", name.upper())
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[\s.,]+", "", ascii_str)


def _iso_to_dmy(iso_date: str) -> str:
    """Convert YYYY-MM-DD → DD/MM/YYYY."""
    try:
        dt = datetime.strptime(iso_date.strip(), "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return iso_date


def _votacion_id(fecha: str, proyecto: str) -> str:
    """Stable 16-char hex ID for a (fecha, proyecto) pair."""
    raw = f"senado_col|{fecha}|{proyecto}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _source_url(fecha_iso: str, proyecto: str) -> str:
    """Construct a datos.gov.co query URL for a specific Senado vote session."""
    return (
        f"{SODA_BASE}/{VOTES_DATASET}.json"
        f"?proyecto={urllib.parse.quote(proyecto, safe='')}"
        f"&fecha={urllib.parse.quote(fecha_iso, safe='')}"
    )


def _dmy_to_iso(dmy: str) -> str:
    """Convert DD/MM/YYYY (with optional time) back to YYYY-MM-DD ISO."""
    try:
        return datetime.strptime(dmy.split(" ")[0].strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        return ""


def _norm_vote(v: str) -> str:
    """Map raw vote text (Si/No/Abstención/…) to canonical uppercase form."""
    s = v.strip().lower()
    if s in ("si", "sí", "s"):
        return "AFIRMATIVO"
    if s in ("no", "n"):
        return "NEGATIVO"
    if "abstenci" in s:
        return "ABSTENCION"
    if "ausen" in s:
        return "AUSENTE"
    return "AFIRMATIVO"


# ---------------------------------------------------------------------------
# Party lookup
# ---------------------------------------------------------------------------

def _build_senator_party_map() -> dict[str, str]:
    """Build norm_key → party from the sjwx-dr6n senator roster dataset."""
    log.info("Loading senator party roster (sjwx-dr6n)...")
    senators = _fetch_all_soda(SENATORS_DATASET)
    party_map: dict[str, str] = {}
    for s in senators:
        name = s.get("nombre", "").strip()
        party = s.get("partido", "").strip()
        if name and party:
            party_map[_norm_key(name)] = party
    log.info(f"Loaded {len(party_map)} senator party entries")
    return party_map


# ---------------------------------------------------------------------------
# Main scraper
# ---------------------------------------------------------------------------

def scrape_senado_colombia() -> None:
    """Scrape Senado de Colombia voting data from datos.gov.co.

    Source dataset: ucmr-52df (Senado de la República — Votaciones plenarias).
    Each unique (fecha, proyecto) pair becomes one votación in the ConsolidatedDB.
    The DB is written to data/senado_col.json in the same format expected by
    generate_site.py / como_voto_generator.
    """
    log.info("=== Scraping Colombian Senado data (datos.gov.co) ===")

    db_path = _DB_DIR / "senado_col.json"
    db = ConsolidatedDB(db_path)
    db.load()
    existing_ids: set[str] = set(db._votacion_ids)
    log.info(f"Existing DB: {len(db.votaciones)} votaciones")

    party_map = _build_senator_party_map()

    log.info("Fetching all vote records from ucmr-52df...")
    records = _fetch_all_soda(VOTES_DATASET, order="fecha ASC")
    log.info(f"Total individual vote records: {len(records)}")

    if not records:
        log.warning("No records returned — skipping Senado scrape.")
        return

    # Group by (fecha, proyecto) → one votacion per pair
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for rec in records:
        fecha = rec.get("fecha", "").strip()
        proyecto = rec.get("proyecto", "").strip()
        if fecha and proyecto:
            groups[(fecha, proyecto)].append(rec)

    log.info(f"Grouped into {len(groups)} votaciones")

    new_count = 0
    for (fecha, proyecto), votes in sorted(groups.items()):
        vid = _votacion_id(fecha, proyecto)
        if vid in existing_ids:
            continue

        afirm = negat = abst = 0
        vote_rows: list[dict] = []

        for rec in votes:
            name = rec.get("fullname", "").strip()
            vote_norm = _norm_vote(rec.get("vote", ""))

            party = party_map.get(_norm_key(name), "")

            vote_rows.append({
                "name": name,
                "bloc": party,
                "province": "",  # Senators are nationally elected
                "vote": vote_norm,
            })

            if vote_norm == "AFIRMATIVO":
                afirm += 1
            elif vote_norm == "NEGATIVO":
                negat += 1
            elif vote_norm == "ABSTENCION":
                abst += 1

        if not vote_rows:
            continue

        result = "AFIRMATIVO" if afirm >= negat else "NEGATIVO"

        db.add_votacion({
            "id": vid,
            "chamber": "senado_col",
            "url": _source_url(fecha, proyecto),
            "title": proyecto[:300],
            "date": _iso_to_dmy(fecha),
            "result": result,
            "type": "EN GENERAL",
            "period": "",
            "afirmativo": afirm,
            "negativo": negat,
            "abstencion": abst,
            "ausente": 0,
            "votes": vote_rows,
        })
        existing_ids.add(vid)
        new_count += 1

    # Backfill source URLs for any existing entries that were stored without one
    backfill_count = 0
    for entry in db.votaciones:
        if not entry.get("url"):
            fecha_iso = _dmy_to_iso(entry.get("d", ""))
            proyecto = entry.get("t", "")
            if fecha_iso and proyecto:
                entry["url"] = _source_url(fecha_iso, proyecto)
                backfill_count += 1
    if backfill_count:
        log.info(f"Backfilled source URLs for {backfill_count} existing Senado entries")

    db.save()
    log.info(f"Senado: +{new_count} votaciones (total: {len(db.votaciones)})")


if __name__ == "__main__":
    scrape_senado_colombia()