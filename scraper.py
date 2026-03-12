#!/usr/bin/env python3
"""Backward-compatible scraper entrypoint and facade.

This module keeps `python scraper.py` and `from scraper import ...` working,
while implementation lives under `como_voto_scraper/`.
"""

from como_voto_scraper import (
    ConsolidatedDB,
    VOTE_DECODE,
    VOTE_ENCODE,
    classify_bloc,
    main,
    scrape_diputados,
    scrape_diputados_photos,
    scrape_hcdn_votacion,
    scrape_senadores,
    scrape_senadores_photos,
)

from como_voto_scraper_colombia import (
    scrape_camara_colombia,
    scrape_senado_colombia,
    scrape_photos_colombia,  # Updated alias for legislator photos in Colombia
)

__all__ = [
    "ConsolidatedDB",
    "VOTE_DECODE",
    "VOTE_ENCODE",
    "classify_bloc",
    "main",
    "scrape_diputados",
    "scrape_hcdn_votacion",
    "scrape_senadores",
    "scrape_diputados_photos",
    "scrape_senadores_photos",
    "scrape_camara_colombia",
    "scrape_senado_colombia",
    "scrape_photos_colombia",
]


if __name__ == "__main__":
    main()
