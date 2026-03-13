# Project Structure

## Overview
"¿Cómo Votó? Colombia" is an interactive visualization platform that tracks how Colombian senators and representatives vote in plenary sessions, their alignment with major political blocs, and historical voting trends. The project targets the **Senado de la República** and the **Cámara de Representantes** of Colombia.

## Directory Structure
```
Como_voto_colombia/
├── scraper.py                          # Entry point for scraping (delegates to packages below)
├── generate_site.py                    # Entry point for data generation (delegates to packages below)
├── requirements.txt                    # Python dependencies
├── README.md                           # Project overview
├── .github/workflows/
│   └── update-data.yml                 # GitHub Actions: daily scrape → generate → deploy
│
├── como_voto_scraper_colombia/         # Colombian-specific scraping package
│   ├── __init__.py                     # Exports scrape_camara_colombia, scrape_senado_colombia, scrape_photos_colombia
│   ├── core_col.py                     # Shared HTTP session, rate-limiting (0.5 s), logging
│   ├── senado_col.py                   # Senado scraper — datos.gov.co SODA API (ucmr-52df)
│   ├── camara_col.py                   # Cámara scraper — camara.gov.co AJAX + ZIP + PDF
│   └── photos_col.py                   # Legislator photo scraper (stub; in progress)
│
├── como_voto_scraper/                  # Shared scraper utilities (originally Argentine)
│   ├── __init__.py
│   ├── db.py                           # ConsolidatedDB: JSON-based votación storage shared by all scrapers
│   ├── core.py                         # Generic vote/bloc classification helpers
│   ├── hcdn.py                         # Argentine Cámara de Diputados scraper (not used for Colombia)
│   ├── senado.py                       # Argentine Senado scraper (not used for Colombia)
│   ├── photos.py                       # Argentine photo scraper (not used for Colombia)
│   └── runner.py                       # CLI for Argentine scrapers
│
├── como_voto_generator/                # Data processing and export package
│   ├── __init__.py                     # Re-exports all public symbols
│   ├── runner.py                       # main(): loads both chambers, sorts, builds law groups, exports
│   ├── common.py                       # Path constants (DATA_DIR, DOCS_DATA_DIR), save_json() helper
│   ├── data_loading.py                 # load_all_votaciones_from_db(), load_photo_maps(), date helpers
│   ├── normalization.py                # Name/vote normalization, Colombian party classification (PH/LIB/CON/CD/CR/OTH)
│   ├── laws.py                         # build_law_groups(), get_common_name() — groups bills across sessions
│   ├── processing.py                   # build_legislator_data(), alignment + majority vote computation
│   └── export.py                       # generate_site_data(): writes all docs/data/ JSON files
│
├── data/                               # Local raw data (not committed to Pages branch)
│   ├── senado_col.json                 # ConsolidatedDB for Senado Colombia
│   ├── camara_col.json                 # ConsolidatedDB for Cámara de Representantes Colombia
│   ├── senadores_col_photos.json       # Senator name → photo filename mapping
│   ├── representantes_photos.json      # Representative name → photo filename mapping
│   ├── bloc_coalition_map.json         # Bloc-name → coalition key mapping (manual overrides)
│   ├── colombia/                       # Additional Colombia-specific raw data
│   └── (legacy Argentine files)        # diputados.json, senadores.json, etc. — not used
│
├── docs/                               # Static site served via GitHub Pages
│   ├── index.html                      # Main SPA shell
│   ├── style.css                       # Stylesheet
│   ├── app.js                          # All frontend logic (search, filters, charts, waffle grid)
│   ├── site.webmanifest                # PWA manifest
│   ├── CNAME                           # Custom domain config
│   └── data/                           # Generated JSON data (written by generate_site.py)
│       ├── legislators.json            # Compact legislator list for search/filter
│       ├── legislators/                # Per-legislator detail files ({key}.json)
│       ├── laws_detail.json            # Per-law vote breakdown by party
│       ├── law_names.json              # Searchable law name index
│       ├── votes/votes_{YYYY}.json     # Per-year compact vote-name tables
│       ├── stats.json                  # Summary statistics (counts, last updated, years covered)
│       ├── votaciones.json             # All votaciones flat list
│       └── colombia_votaciones.json    # Colombia-specific votaciones
│
├── tests/                              # Unit tests
│   ├── test_normalization.py
│   └── test_processing.py
│
└── tools/                              # Development and diagnostic scripts
    ├── serve.py                        # Local dev server for docs/
    ├── build_bloc_map.py               # Build bloc_coalition_map.json from scraped data
    ├── verify_coalitions.py            # Sanity-check coalition assignments
    ├── check_legislator_files.py       # Verify per-legislator JSON completeness
    ├── probe_camara*.py / probe_col*.py # Exploratory probes used during scraper development
    └── legacy/                         # Archived scripts
```

## Key Modules

| Module | Role |
|--------|------|
| `como_voto_scraper_colombia/` | Fetches raw plenary vote records from Colombian government sources |
| `como_voto_scraper/db.py` | `ConsolidatedDB` persistence layer — shared by both chambers |
| `como_voto_generator/normalization.py` | Canonical vote types, name matching, Colombian party classification |
| `como_voto_generator/processing.py` | Per-legislator aggregation, alignment and majority computation |
| `como_voto_generator/export.py` | Writes all static JSON files consumed by the frontend |
| `docs/app.js` | Single-page frontend: search, filters, waffle grid, charts, law search |

## Data Flow
```
[camara.gov.co AJAX + PDF]  →  camara_col.py  →  data/camara_col.json  ┐
[datos.gov.co SODA API]     →  senado_col.py  →  data/senado_col.json  ┘
                                                         ↓
                              como_voto_generator/runner.py
                                     ↓
                              docs/data/*.json   →   GitHub Pages SPA
```