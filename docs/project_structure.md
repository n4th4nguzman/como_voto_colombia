# Project Structure

## Overview
The "¿Cómo Votó?" project is an interactive visualization platform that tracks how Argentine legislators vote, their alignment with major political parties, and historical voting trends.

## Directory Structure
```
Como_voto/
├── scraper.py                 # Entry point for scraping
├── generate_site.py           # Entry point for data generation
├── requirements.txt           # Python dependencies
├── README.md                  # Project overview
├── .github/workflows/         # GitHub Actions for automation
│   └── update-data.yml        # Daily scrape, generate, and deploy
├── como_voto_scraper/         # Scraping package
│   ├── __init__.py            # Package initialization
│   ├── runner.py              # CLI and orchestration
│   ├── db.py                  # SQLite + JSON database utilities
│   ├── hcdn.py                # Scraper for Cámara de Diputados
│   ├── senado.py              # Scraper for Senado
│   ├── photos.py              # Scraper for legislator photos
│   └── core.py                # Utilities for classification
├── como_voto_generator/       # Data generation package
│   ├── __init__.py            # Package initialization
│   ├── runner.py              # CLI and orchestration
│   ├── data_loading.py        # Data loading and preprocessing
│   ├── processing.py          # Data processing and aggregation
│   ├── laws.py                # Law grouping and naming
│   ├── normalization.py       # Data normalization
│   ├── export.py              # JSON export for frontend
│   └── common.py              # Common utilities
├── data/                      # Local database (JSON + SQLite)
│   ├── diputados.json         # Raw Diputados data
│   ├── senadores.json         # Raw Senadores data
│   ├── diputados_photos.json  # Diputados photo mapping
│   ├── senadores_photos.json  # Senadores photo mapping
│   ├── bloc_coalition_map.json# Bloc-to-coalition mapping
│   └── election_legislators.json # Legislators by election
├── docs/                      # Static site for GitHub Pages
│   ├── index.html             # Main frontend
│   ├── style.css              # Stylesheet
│   ├── app.js                 # Frontend logic
│   └── data/                  # JSON data for frontend
├── tools/                     # Auxiliary scripts
│   ├── serve.py               # Local development server
│   ├── build_bloc_map.py      # Generate bloc mapping
│   ├── verify_coalitions.py   # Verify coalitions
│   ├── scrape_elections.py    # Scrape election data
│   ├── check_legislator_files.py  # Verify legislator files
│   └── legacy/                # Legacy scripts
```

## Key Modules
- **como_voto_scraper/**: Handles data scraping from legislative websites.
- **como_voto_generator/**: Processes and normalizes data for frontend use.
- **data/**: Stores raw and processed data in JSON format.
- **docs/**: Contains the static site for visualization.
- **tools/**: Provides auxiliary scripts for development and maintenance.