# Endpoints Documentation

This document lists all the endpoints used by the "¿Cómo Votó?" project to gather legislative data, along with the type of information retrieved.

## Endpoints

### 1. Cámara de Diputados (HCDN)
- **Base URL**: `https://votaciones.hcdn.gob.ar`
- **Endpoints**:
  - `/votacion/{id}`: Retrieves detailed voting data for a specific law or session.
  - `/votacion/{slug}/{id}`: Retrieves voting data for specific cases where a slug is required (e.g., Derecho Identidad de Género).
- **Data Retrieved**:
  - Voting results (affirmative, negative, abstentions)
  - Legislator participation
  - Law titles and descriptions

### 2. Senado
- **Base URL**: `https://www.senado.gob.ar`
- **Endpoints**:
  - `/votaciones/actas`: Retrieves a list of voting sessions (actas) for a given year.
  - `/votaciones/detalleActa/{id}`: Retrieves detailed voting data for a specific session.
- **Data Retrieved**:
  - Voting results (affirmative, negative, abstentions)
  - Legislator participation
  - Session details (date, type, result)

## Summary
The project relies on endpoints from the Cámara de Diputados and Senado to scrape legislative data. These endpoints provide detailed voting results, legislator participation, and session metadata, which are processed and normalized for visualization.