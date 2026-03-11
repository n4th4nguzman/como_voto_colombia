# ¿Cómo Votó? 🗳️

Visualización interactiva de cómo votan los Diputados y Senadores de la Nación Argentina, y su alineamiento con los principales partidos políticos.

## 🌐 Ver el sitio

👉 **[Abrir ¿Cómo Votó?](https://rquiroga7.github.io/Como_voto/)**

## 📊 ¿Qué muestra?

- **Buscador** de todos los Diputados y Senadores de la Nación
- **Visualización waffle/grilla** de los votos de cada legislador, agrupados por ley
- **Nombres comunes de leyes** (ej: "Ley Bases", "Reforma Laboral" en vez de títulos formales)
- **Agrupación inteligente**: votos EN GENERAL + EN PARTICULAR de la misma ley se muestran juntos
- **Cruce entre cámaras**: legisladores que fueron Diputados y Senadores aparecen unificados
- **Historial de votos** con filtros por año, tipo de voto y nombre de ley
- **Alineamiento por año** con las coaliciones principales:
  - **PJ** (Partido Justicialista / Frente de Todos / Frente para la Victoria / Unión por la Patria)
  - **PRO** (PRO / Cambiemos / Juntos por el Cambio / UCR)
  - **LLA** (La Libertad Avanza)
- **Gráficos interactivos** de distribución de votos y tendencia de alineamiento
- **Exportar imagen** de la grilla para compartir en redes sociales

## 🏗️ Arquitectura

```
Como_voto/
├── scraper.py                 # Entry point (fachada hacia como_voto_scraper/)
├── generate_site.py           # Entry point (fachada hacia como_voto_generator/)
├── requirements.txt           # Dependencias Python
├── README.md                  # Este archivo
├── .github/workflows/
│   └── update-data.yml        # GitHub Action: scrape + generate + deploy diario
│
├── como_voto_scraper/         # Paquete de scraping (implementación real)
│   ├── __init__.py            # Exports de la fachada
│   ├── runner.py              # Main CLI y orquestación
│   ├── db.py                  # ConsolidatedDB: SQLite + JSON, VOTE_ENCODE/DECODE
│   ├── hcdn.py                # Scraper Cámara de Diputados (votaciones.hcdn.gob.ar)
│   ├── senado.py              # Scraper Senado (senado.gob.ar/votaciones/actas)
│   ├── photos.py              # Scraper de fotos de legisladores
│   └── core.py                # Utilidades: classify_bloc, etc.
│
├── como_voto_generator/       # Paquete de generación de datos (implementación real)
│   ├── __init__.py            # Exports de la fachada
│   ├── runner.py              # Main CLI y orquestación
│   ├── data_loading.py        # Carga desde DB/JSON, attach_photos, practical_year_range
│   ├── processing.py          # Construcción de datos por legislador, majority vote
│   ├── laws.py                # Agrupación de leyes, nombres comunes (COMMON_NORM)
│   ├── normalization.py       # Normalización de nombres, provincias, votos, bloques
│   ├── export.py              # Generación de JSON para frontend (alignment, terms)
│   └── common.py              # Utilidades: save_json, etc.
│
├── data/                      # Base de datos local (JSON + SQLite)
│   ├── diputados.json         # Votaciones Diputados (raw)
│   ├── senadores.json         # Votaciones Senadores (raw)
│   ├── diputados_photos.json  # Mapeo de fotos Diputados
│   ├── senadores_photos.json  # Mapeo de fotos Senadores
│   ├── hcdn_slug_map.json     # Mapeo de slugs HCDN
│   ├── bloc_coalition_map.json# Mapeo bloques → coaliciones
│   └── election_legislators.json # Legisladores por elección
│
├── docs/                      # Sitio web (GitHub Pages)
│   ├── index.html             # Frontend principal
│   ├── style.css              # Estilos
│   ├── app.js                 # Lógica frontend
│   └── data/                  # JSON generados para el frontend
│       ├── stats.json         # Estadísticas generales
│       ├── legislators.json   # Lista de legisladores
│       ├── votaciones.json    # Detalle de votaciones
│       ├── law_names.json     # Nombres comunes de leyes
│       └── legislators/       # Un archivo por legislador (datos waffle)
│
├── tools/                     # Herramientas auxiliares
│   ├── serve.py               # Servidor local para desarrollo
│   ├── build_bloc_map.py      # Generar mapeo de bloques
│   ├── verify_coalitions.py   # Verificar coaliciones
│   ├── scrape_elections.py    # Scrape datos de elecciones
│   ├── check_legislator_files.py  # Verificar archivos de legisladores
│   └── legacy/                # Scripts legacy (mantenidos por compatibilidad)
│
└── tests/                     # Tests unitarios
    ├── test_normalization.py  # Tests de normalización
    └── test_processing.py     # Tests de procesamiento
```

## 🚀 Uso

### Requisitos

- Python 3.10+
- pip

### Instalación

```bash
pip install -r requirements.txt
```

### Recolectar datos

```bash
# Scrape ambas cámaras
python scraper.py

# Solo Diputados
python scraper.py diputados

# Solo Senadores
python scraper.py senadores
```

El scraper **no vuelve a descargar** votaciones que ya están en `data/`. Solo descarga las nuevas.

### Generar el sitio

```bash
python generate_site.py
```

Esto genera los archivos JSON en `docs/data/` que son consumidos por el frontend.

### Ver localmente

Podés abrir `docs/index.html` directamente en el navegador, o usar un servidor local:

```bash
python tools/serve.py
```

O alternativamente:

```bash
cd docs
python -m http.server 8000
```

Y visitar `http://localhost:8000`

## 📡 Fuentes de datos

- **Diputados**: [votaciones.hcdn.gob.ar](https://votaciones.hcdn.gob.ar/)
- **Senadores**: [senado.gob.ar/votaciones/actas](https://www.senado.gob.ar/votaciones/actas)

> La información contenida en estos sitios es de dominio público y puede ser utilizada libremente (según las propias fuentes).

## 🔄 Actualización automática

El GitHub Action `update-data.yml` se ejecuta automáticamente todos los días a las 07:00 UTC (04:00 GMT-3), recolecta nuevas votaciones y actualiza el sitio. También puede ejecutarse manualmente desde la pestaña "Actions" del repositorio.

## 🧪 Tests

```bash
python -m pytest tests/
```

## 📜 Licencia

MIT
