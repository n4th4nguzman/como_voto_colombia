from __future__ import annotations

import json
import os
import re

from scraper import ConsolidatedDB

from .common import DATA_DIR, DOCS_DIR, log
from .normalization import NAME_ALIASES, normalize_name


def load_all_votaciones_from_db(chamber: str) -> list[dict]:
    """Carga todas las votaciones desde un archivo de base consolidada."""
    db_path = DATA_DIR / f"{chamber}.json"
    if not db_path.exists():
        log.warning(f"Consolidated DB not found: {db_path}")
        return []

    db = ConsolidatedDB(db_path)
    db.load()
    log.info(f"Loaded {len(db.votaciones)} {chamber} votaciones from DB")
    return db.expand_all(chamber)


def clean_date(date_str: str) -> str:
    """Limpia una fecha: extrae DD/MM/YYYY y opcionalmente HH:MM."""
    date_match = re.search(r"(\d{2}/\d{2}/\d{4})", date_str)
    if not date_match:
        return date_str.strip()

    result = date_match.group(1)
    time_match = re.search(r"(\d{2}:\d{2})", date_str)
    if time_match:
        result += " - " + time_match.group(1)
    return result


def extract_year(date_str: str) -> int | None:
    match = re.search(r"(\d{4})", date_str)
    if match:
        return int(match.group(1))
    return None


def practical_year_range(years_list: list[str]) -> tuple[str | None, str | None]:
    """Devuelve (año_mínimo, año_máximo) ignorando outliers tempranos aislados."""
    if not years_list:
        return None, None

    ints = sorted(int(year) for year in years_list)
    start = ints[0]
    if len(ints) > 1 and (ints[1] - ints[0]) > 10:
        start = ints[1]
    return str(start), str(ints[-1])


def _reverse_name_order(name: str) -> str:
    """Swap first-half and second-half of a name to handle Nombre↔Apellido reordering.

    The Cámara website stores names as 'Nombre1 Nombre2 Apellido1 Apellido2' while
    the PDFs (and thus the DB) store them as 'Apellido1 Apellido2 Nombre1 Nombre2'.
    For 4+-word names this uses a midpoint split; for 3 words it shifts by 1; for
    2 words it reverses the pair.
    """
    parts = name.split()
    if len(parts) >= 4:
        mid = len(parts) // 2
        return " ".join(parts[mid:] + parts[:mid])
    elif len(parts) == 3:
        return " ".join(parts[1:] + parts[:1])
    elif len(parts) == 2:
        return " ".join(reversed(parts))
    return name


def load_photo_maps() -> dict[str, str]:
    """Carga mapeos nombre->archivo de foto generados por el scraper."""
    photo_map: dict[str, str] = {}

    for photo_file in ["representantes_photos.json", "senadores_col_photos.json"]:
        photos_path = DATA_DIR / photo_file
        is_rep = photo_file.startswith("representantes")
        if photos_path.exists():
            try:
                with open(photos_path, "r", encoding="utf-8") as handle:
                    photos = json.load(handle)
                for name, filename in photos.items():
                    name_key = normalize_name(name)
                    photo_path = f"fotos/{filename}"
                    if name_key not in photo_map:
                        photo_map[name_key] = photo_path
                    # For representatives, the website uses Nombre-first ordering
                    # while the DB (from PDFs) uses Apellido-first.  Add both a
                    # reversed-order spaced key and a no-space variant so either
                    # format can match.
                    if is_rep:
                        rev_key = normalize_name(_reverse_name_order(name))
                        for key in (rev_key, rev_key.replace(" ", ""), name_key.replace(" ", "")):
                            if key not in photo_map:
                                photo_map[key] = photo_path
                    else:
                        no_space_key = name_key.replace(" ", "")
                        if no_space_key not in photo_map:
                            photo_map[no_space_key] = photo_path
            except (json.JSONDecodeError, OSError):
                pass

    # Propagate photos across aliases: if the canonical key has no photo but
    # its alias does (or vice-versa), copy it over so merged records get a photo.
    for alias_key, canon_key in NAME_ALIASES.items():
        if canon_key not in photo_map and alias_key in photo_map:
            photo_map[canon_key] = photo_map[alias_key]

    return photo_map


def attach_photos(legislators: dict, photo_map: dict[str, str]) -> None:
    """Adjunta rutas de foto a los registros de legisladores."""
    matched = 0
    for name_key, leg in legislators.items():
        photo = photo_map.get(name_key, "")
        if photo:
            full_path = DOCS_DIR / photo.replace("/", os.sep)
            if full_path.exists():
                leg["photo"] = photo
                matched += 1
            else:
                leg["photo"] = ""
        else:
            leg["photo"] = ""
    log.info(f"Attached photos to {matched}/{len(legislators)} legislators")
