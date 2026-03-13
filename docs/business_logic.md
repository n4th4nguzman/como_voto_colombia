# Business Logic and Workflows

## Overview
"¿Cómo Votó? Colombia" tracks how Colombian senators (Senado de la República) and representatives (Cámara de Representantes) vote in plenary sessions. The pipeline scrapes raw voting data from open government APIs and official chamber websites, normalizes it, and builds a static JSON dataset consumed by an interactive frontend.

## Workflows

### 1. Data Scraping
- **Objective**: Collect plenary voting records and legislator roster data for both chambers.
- **Module**: `como_voto_scraper_colombia/`
- **Senado de Colombia** (`senado_col.py`):
  1. Fetch all individual vote records from the datos.gov.co SODA dataset `ucmr-52df` (paginated, 10 000 records/page).
  2. Load senator party affiliations from SODA dataset `sjwx-dr6n`.
  3. Group individual rows by `(fecha, proyecto)` pairs to form a single *votación* per bill per day.
  4. Assign a stable 16-character MD5-based ID to each votación.
  5. Persist results to `data/senado_col.json` via `ConsolidatedDB`.
- **Cámara de Representantes** (`camara_col.py`):
  1. Fetch a WordPress AJAX nonce from `camara.gov.co/secretaria-general/actas-votaciones-y-otros/`.
  2. Paginate through plenary session listings (10 sessions/page) using the `get_actas_y_otros_page` AJAX action.
  3. For each session, download the accompanying ZIP file containing a PDF voting record.
  4. Parse the PDF with `pdfplumber`: extract the attendance list and split the document into numbered `VOTACION` blocks.
  5. Cross-reference legislator names against the datos.gov.co roster dataset `5pt5-nxdp` to attach party and department.
  6. Persist results to `data/camara_col.json` via `ConsolidatedDB`.
- **Storage format**: Both chamber databases use the shared `ConsolidatedDB` JSON schema (same format as the original Argentine scrapers), making the downstream generator chamber-agnostic.

### 2. Vote Normalization
- **Objective**: Map raw source values to canonical vote types.
- **Module**: `como_voto_generator/normalization.py`
- Raw values from the Senado SODA API (`Si`, `Sí`, `No`, `Abstención`, `Ausente`) and Cámara PDFs (`Sí`/`Sφ` font artifacts, `No`, `Abstenci…`) are all mapped to four canonical types:
  - `AFIRMATIVO` — affirmative vote
  - `NEGATIVO` — negative vote
  - `ABSTENCION` — abstention
  - `AUSENTE` — absent from vote
- Legislator names are ASCII-normalized and uppercased for cross-source matching.
- Party/bloc names are classified into six canonical Colombian party keys: **PH** (Pacto Histórico / left bloc), **LIB** (Partido Liberal), **CON** (Partido Conservador), **CD** (Centro Democrático), **CR** (Cambio Radical), **OTH** (all others).

### 3. Data Processing
- **Objective**: Aggregate per-vote rows into per-legislator profiles and per-law summaries.
- **Module**: `como_voto_generator/`
- **Steps**:
  1. Load all votaciones from `data/camara_col.json` and `data/senado_col.json` and sort chronologically.
  2. Group votaciones into *law groups* (bills that appear in multiple sessions) using `laws.py`.
  3. Build per-legislator records: total votes cast, alignment over time, party/coalition history, years active, and per-law vote detail.
  4. Compute majority positions per coalition for each votación to identify contested vs. uncontested votes.
  5. Attach photo filenames from `data/representantes_photos.json` and `data/senadores_col_photos.json`.

### 4. Data Export
- **Objective**: Produce optimised static JSON files consumed directly by the browser.
- **Module**: `como_voto_generator/export.py`
- **Output files** (all written to `docs/data/`):
  - `legislators.json` — compact list of all legislators (name, chamber, coalition, province, photo, total votes).
  - `legislators/{key}.json` — full per-legislator detail (vote history, alignment chart series, party timeline).
  - `laws_detail.json` — per-law vote breakdown tallied by the six party keys.
  - `law_names.json` — searchable law name index.
  - `votes/votes_{YYYY}.json` — compact per-year vote-name tables (integer-indexed to minimise payload).
  - `stats.json` — summary statistics (last update timestamp, counts of legislators, votaciones, years covered).
  - `votaciones.json` / `colombia_votaciones.json` — raw votación data.
- JSON is written atomically via a `.tmp` + rename pattern to avoid partial reads.

### 5. Frontend Visualization
- **Objective**: Present data interactively in a static single-page application.
- **Location**: `docs/`
- **Features**:
  - Full-text search by legislator name, party/bloc, or department.
  - Filter by chamber (`Sen.` / `Rep.`), coalition, and department.
  - Waffle/grid visualization of votes grouped by law and year.
  - Alignment chart (line + bar) showing voting alignment trend over time.
  - Vote history table with pagination (25 votes/page).
  - Law search with per-party (PH / LIB / CON / CD / CR / Otros) vote breakdown.
  - Share to social media and copy-as-image actions.

## Party / Coalition Classification

| Key | Coalition | Main parties included |
|-----|-----------|----------------------|
| `PH` | Pacto Histórico | Colombia Humana, Unión Patriótica, Polo Democrático, Marcha Patriótica, Comunes, MAIS, Alianza Verde |
| `LIB` | Partido Liberal | Partido Liberal Colombiano |
| `CON` | Partido Conservador | Partido Conservador Colombiano, Colombia Conservadora |
| `CD` | Centro Democrático | Centro Democrático |
| `CR` | Cambio Radical | Cambio Radical |
| `OTH` | Otros / Independent | All remaining parties |

## Current Data Coverage (as of last scrape)
- **Total legislators**: 201 (all Senado)
- **Total laws**: 241
- **Years covered**: 2017 – 2024 (Senado); Cámara data pending
- **Cámara de Representantes**: scraper implemented; data ingestion in progress

## Automation
- **GitHub Actions** (`update-data.yml`): automates daily scraping, processing, and deployment to GitHub Pages.
- **Entry points**: `python scraper.py` (scraping) → `python generate_site.py` (generation).

## Data Integrity
- Existing votación IDs are preserved across scrape runs; only new records are appended.
- A stable hash-based ID (MD5 of `chamber|date|project`) prevents duplicate ingestion.
- Atomic JSON writes prevent partially-written files from corrupting the frontend.
