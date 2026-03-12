# Business Logic and Workflows

## Overview
The "¿Cómo Votó?" project follows a structured workflow to scrape, process, and visualize legislative data. The business logic ensures data accuracy, normalization, and effective presentation.

## Workflows
### 1. Data Scraping
- **Objective**: Collect legislative voting data, legislator photos, and metadata.
- **Tools**: `como_voto_scraper/`
- **Steps**:
  1. Scrape voting data from Cámara de Diputados and Senado websites.
  2. Scrape legislator photos and metadata.
  3. Store raw data in JSON format.

### 2. Data Processing
- **Objective**: Normalize and aggregate raw data for visualization.
- **Tools**: `como_voto_generator/`
- **Steps**:
  1. Load raw data from `data/`.
  2. Normalize legislator names, provinces, and votes.
  3. Group laws by common names and categories.
  4. Aggregate voting data by legislator and coalition.

### 3. Data Export
- **Objective**: Generate JSON files for frontend visualization.
- **Tools**: `como_voto_generator/export.py`
- **Steps**:
  1. Export aggregated data to `docs/data/`.
  2. Generate JSON files for legislators, votes, laws, and statistics.

### 4. Frontend Visualization
- **Objective**: Present data interactively to users.
- **Tools**: `docs/`
- **Steps**:
  1. Load JSON data into the frontend.
  2. Render interactive visualizations (waffle/grid, graphs).
  3. Enable filtering by year, vote type, and law name.

## Key Components
- **Scraping**: Ensures up-to-date legislative data.
- **Normalization**: Guarantees data consistency.
- **Visualization**: Provides an intuitive and interactive user experience.

## Automation
- **GitHub Actions**: Automates daily scraping, processing, and deployment.
- **update-data.yml**: Runs the entire workflow pipeline daily.

## Summary
The project’s business logic ensures accurate, normalized, and visually appealing data presentation. The workflows are automated to maintain up-to-date information with minimal manual intervention.