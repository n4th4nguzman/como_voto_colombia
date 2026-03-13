# Endpoints Documentation

This document lists all external sources used by "¿Cómo Votó? Colombia" to gather legislative data.

---

## 1. Senado de Colombia — datos.gov.co SODA API

All Senado data is fetched from Colombia's open-data portal via the Socrata Open Data API (SODA).

### Vote records dataset (`ucmr-52df`)
- **Base URL**: `https://www.datos.gov.co/resource/ucmr-52df.json`
- **Used by**: `como_voto_scraper_colombia/senado_col.py`
- **Method**: GET with `$limit=10000` and `$offset` for pagination; sorted `fecha ASC`
- **Data retrieved**:
  - `fecha` — vote date (ISO `YYYY-MM-DD`)
  - `proyecto` — bill or agenda item name
  - full senator name
  - vote value (`Si` / `No` / `Abstención` / `Ausente`)
- **Grouping logic**: Each unique `(fecha, proyecto)` pair is treated as one *votación*.

### Senator roster dataset (`sjwx-dr6n`)
- **Base URL**: `https://www.datos.gov.co/resource/sjwx-dr6n.json`
- **Used by**: `como_voto_scraper_colombia/senado_col.py` (`_build_senator_party_map`)
- **Method**: GET (single page, full dataset)
- **Data retrieved**:
  - Senator full name (`nombre`)
  - Party affiliation (`partido`)
- **Purpose**: Enriches each vote row with the senator's party for coalition classification.

---

## 2. Cámara de Representantes — camara.gov.co

The Cámara website does not expose a public API. The scraper uses the site's internal WordPress AJAX mechanism and downloads session ZIP archives containing PDF voting records.

### Nonce endpoint (CSRF token)
- **URL**: `https://www.camara.gov.co/secretaria-general/actas-votaciones-y-otros/`
- **Method**: GET
- **Purpose**: Extracts the WordPress nonce (`AY_NONCE`) required for all subsequent AJAX calls.

### Session listing (AJAX)
- **URL**: `https://www.camara.gov.co/wp-admin/admin-ajax.php`
- **Method**: POST
- **Key form fields**:
  - `action=get_actas_y_otros_page`
  - `_ajax_nonce={nonce}`
  - `tipo=Sesiones Plenarias`
  - `comision=Secretaría General`
  - `page={n}` (10 sessions/page)
- **Data retrieved**: List of plenary sessions, each with a `enlace` (ZIP download URL) and session date.

### Session ZIP download
- **URL**: `{enlace}` from session listing (absolute or relative to `https://www.camara.gov.co`)
- **Method**: GET
- **Content**: A ZIP file containing one or more PDFs with the official electronic voting record.

### Voting PDF
- **Format**: "Registro asistencia y votacion Electrónica" — a structured PDF parsed with `pdfplumber`.
- **Structure**:
  - Preamble: numbered attendance list (legislators present).
  - Repeated `VOTACION N` blocks, each with: vote title, start time, results summary, per-legislator `Sí/No/Abstención` table.

---

## 3. Cámara de Representantes — datos.gov.co Roster

### Representatives roster dataset (`5pt5-nxdp`)
- **Base URL**: `https://www.datos.gov.co/resource/5pt5-nxdp.json?$limit=300`
- **Used by**: `como_voto_scraper_colombia/camara_col.py` (`_build_camara_roster`)
- **Method**: GET
- **Data retrieved**:
  - Representative full name (`_` column)
  - Department (`apelidos_y_nombre` — mislabelled in source)
  - Party (`partido_o_movimiento`)
- **Note**: Column names in the source dataset are mislabelled; the scraper handles this explicitly. Names are stored in both original and reversed `apellidos+nombres` order to maximise PDF cross-matching.

---

## Rate Limiting

All requests are subject to a default 0.5-second delay between calls (configurable via `REQUEST_DELAY` in `core_col.py`). The shared `requests.Session` sends a civic-project `User-Agent` and `Accept-Language: es-CO` on every request.

---

## Canonical Vote Mapping

| Raw value (source) | Canonical type |
|--------------------|----------------|
| `Si`, `Sí`, `S`, `Sφ` (PDF font artifact) | `AFIRMATIVO` |
| `No`, `N` | `NEGATIVO` |
| `Abstención`, `Abstencion`, `abstenci…` | `ABSTENCION` |
| `Ausente`, `ausen…` | `AUSENTE` |