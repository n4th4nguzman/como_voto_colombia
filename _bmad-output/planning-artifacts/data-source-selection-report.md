Alineamiento Político en Votaciones Divididas# Reporte: Selección de fuentes de datos para ¿Cómo Votó? Colombia

**Fecha:** Marzo 2026  
**Propósito:** Documentar qué fuentes de datos se exploraron, qué obstáculos se encontraron, y por qué se llegó a la arquitectura actual (SODA API para el Senado + ZIP/PDF para la Cámara).

---

## Resumen ejecutivo

Al inicio del proyecto se esperaba encontrar APIs o páginas web con datos tabulares legibles directamente — como las que existen en Argentina (HCDN/Senado) y como las que ofrecen portales como **Congreso Visible** (uniandes.edu.co). La exploración mostró que ninguna de las instituciones colombianas expone sus votaciones mediante una API pública moderna o un sistema de consulta interactivo fácilmente scrappeable. La única fuente estructurada disponible y completa para el Senado resultó ser el portal de datos abiertos `datos.gov.co`; para la Cámara no existe un equivalente y los únicos registros oficiales son archivos ZIP/PDF publicados en el sitio web institucional.

---

## Fuentes exploradas y resultado de cada exploración

### 1. Congreso Visible — congresovisible.uniandes.edu.co

**Tipo:** Portal académico de la Universidad de los Andes.  
**Exploración:** No se hizo un probe automatizado de esta URL, pero fue considerada durante el diseño. El portal Congreso Visible es principalmente una base de datos de seguimiento a proyectos de ley (trayectoria legislativa, ponentes, comisiones), **no un registro sistematizado de votaciones nominales por legislador**. Sus datos de votación son resúmenes agregados, no registros individuales (`nombre → voto`), que es exactamente la granularidad que el proyecto necesita para construir perfiles por legislador.  
**Veredicto:** ❌ No provee votaciones nominales individuales. Descartado como fuente principal.

---

### 2. senado.gov.co — sitio web oficial del Senado

**Archivos de exploración:** `probe_senado.py`, `probe_senado2.py`, `probe_senado3.py`, `probe_senado4.py`, `probe_senado5.py`

**Lo que se intentó:**

| Prueba | URL intentada | Resultado |
|--------|--------------|-----------|
| `probe_senado.py` | `/votaciones`, `/sesiones/actas`, `/index.php/actas-y-votaciones` | HTTP 404 o redireccionamientos sin contenido útil |
| `probe_senado.py` | `congreso.gov.co`, `leyes.senado.gov.co` | Accesibles pero sin datos de votación nominal |
| `probe_senado2.py` | Navegación por links del home de senado.gov.co buscando "vot\|acta\|sesion" | Links encontrados llevan a PDFs manuales y reseñas de sesiones, no a registros de votos |
| `probe_senado3.py` | `secretariasenado.gov.co` (Secretaría del Senado) | El sitio tiene páginas por cuatrienio/legislatura/plenaria pero cada jornada enlaza a PDFs de actas, sin ninguna API ni tabla HTML |
| `probe_senado4.py` | Página de julio 2023 en secretariasenado.gov.co | Sólo links a archivos `.pdf` del acta narrativa; no hay "Registro Electrónico de Votación" en formato estructurado |
| `probe_senado5.py` | Día específico de plenaria (20 jul 2023) | Únicamente PDF del acta narrativa y algunos documentos `.doc`; ningún XLS/CSV/JSON |

**Obstáculo infranqueable:** El sitio web del Senado no publica los resultados nominales de votación en ningún formato estructurado (HTML, JSON, CSV, XLS). Los archivos disponibles son actas narrativas en PDF, que no tienen un formato regular y no incluyen la lista completa de "senador X votó Y".

**Veredicto:** ❌ Descartado. No existe una API ni tablas HTML scrapeables con votaciones nominales.

---

### 3. camara.gov.co — sitio web oficial de la Cámara de Representantes

**Archivos de exploración:** `probe_camara.py` a `probe_camara7.py`, `probe_camara_zip.py`, `probe_camara_pdf.py`, `probe_camara_pdf2.py`, `probe_camara_votes.py`, `debug_nonce.py`, `list_zip_contents.py`

**Lo que se intentó (en orden cronológico):**

#### 3a. Datos abiertos y APIs directas
| Prueba | URL | Resultado |
|--------|-----|-----------|
| `probe_camara.py` | `/secretaria/datos-abiertos`, `/api/v1/votaciones`, `/votaciones`, `opendata.camara.gov.co` | 404 o páginas genéricas sin datos de votación; `/api/v1/votaciones` no existe |
| `probe_camara.py` | `/votaciones` | Página existe pero no tiene tablas HTML ni JSON incrustado con registros de votos |
| `probe_camara2.py` | `/transparencia/datos-abiertos/seccion-de-datos-abiertos/` | Lista links a documentos institucionales; ninguno es un dataset de votaciones |
| `probe_camara2.py` | `/votaciones` | No hay tablas HTML; los pocos links de "año" conducen a páginas de sesiones que sólo listan actas en PDF |
| `probe_camara3.py` | `/secretaria-general/actas-votaciones-y-otros/` | ✅ Página de interés encontrada — contiene un listado de sesiones plenarias, pero el contenido se carga **dinámicamente vía JavaScript (WordPress AJAX)** |

#### 3b. Descubrimiento del mecanismo AJAX
| Prueba | Hallazgo |
|--------|---------|
| `probe_camara4.py` | Se encontró que la página `/secretaria-general/actas-votaciones-y-otros/` usa WordPress; se intentaron acciones AJAX genéricas (`get_actas_votaciones`, `load_actas`, `ap_get_actas`, `ay_get_actas`) → todas devuelven error |
| `probe_camara5.py` | Se encontró la acción AJAX correcta: **`get_actas_y_otros_page`** con nonce `AY_NONCE` embebido en el JavaScript inline de la página |
| `probe_camara6.py` | Se confirmó el patrón JS: `window.AY_NONCE = "11703efb1c"` (el valor cambia con cada deploy) |
| `probe_camara7.py` | Se validó que el endpoint AJAX devuelve JSON con `{ items: [...], total_pages: N }` — cada ítem tiene `id`, `titulo`, `enlace` (URL del ZIP) y `fecha_iso` |

El AJAX era la única vía para obtener el índice de sesiones de forma automatizada. No existe un sitemap ni RSS con URLs directas a los ZIPs.

#### 3c. Inspección del contenido de los ZIPs
| Prueba | Hallazgo |
|--------|---------|
| `probe_camara_zip.py` | Se descargó el ZIP de la sesión 124586 (26/11/2025). Contenido: varios PDFs sin extensión uniforme ni CSV/XLS |
| `probe_camara_pdf.py` | Se probó `pdfplumber.extract_tables()` en el PDF de votación — las **tablas estructuradas** no se extraen correctamente porque el PDF usa diseño de columnas sin bordes de tabla reales |
| `probe_camara_pdf2.py` | Se probó extracción de texto crudo con `layout=True` — el texto fluye continuamente, no en columnas separadas por delimitadores |
| `probe_camara_votes.py` | Se localizó el PDF correcto dentro del ZIP: "Registro asistencia y votacion Electrónica" (distinguible por nombre con "votac" en el basename). Al leer todas las páginas, se encontró que el documento tiene una estructura repetible: secciones `VOTACION N` con título, resultados (Afirmativos/Negativos/Abstenciones) y una lista `1. NOMBRE  VOTO` en texto plano |

**Obstáculo:** El PDF no usa tablas HTML ni XML interno; es texto plano renderizado con fuentes especiales que a veces producen artefactos (`Sí` aparece como `Sφ`, `ó` como `≤`). Se desarrollaron expresiones regulares específicas para parsear estos bloques y normalizar los artefactos tipográficos.

**Veredicto:** ✅ **ZIP + PDF es la única fuente de votaciones nominales de la Cámara**. No existe ninguna API ni dataset público con este nivel de granularidad. Se implementó extracción via `pdfplumber` con regex sobre el texto crudo.

---

### 4. datos.gov.co — Portal de datos abiertos de Colombia

**Archivos de exploración:** `probe_colombia_api.py`, `search_col_datasets.py`, `probe_col2.py`, `probe_col3.py`, `probe_col4.py`, `probe_col5.py`, `probe_col_parties.py`, `probe_col_parties2.py`, `probe_camara_roster.py`

Este fue el camino más fructífero para el Senado.

#### 4a. Búsqueda de datasets de votaciones

| Prueba | Dataset ID | Nombre | Resultado |
|--------|-----------|--------|-----------|
| `probe_colombia_api.py` | `ucmr-52df` | Votaciones Sesiones Plenaria del Senado | ✅ Contiene registros individuales por senador con fecha, proyecto y voto |
| `probe_colombia_api.py` | `w4na-y7b4`, `r97q-dra7`, `7ghe-6btm` | Posibles datasets Cámara | ❌ Vacíos o no encontrados |
| `search_col_datasets.py` | Búsquedas: "votaciones congreso", "camara representantes votos", etc. | — | ❌ No apareció ningún dataset de votaciones nominales para la Cámara en el catálogo |
| `probe_col5.py` | `u3jn-rge3`, `5t2d-p4s8`, `q68v-6cak`, `qe3f-mf23`, `4tvb-s7bi` | IDs probados por fuerza bruta | ❌ Todos vacíos o con error |

**Conclusión crítica:** `ucmr-52df` es el **único dataset en datos.gov.co con votaciones nominales individuales**, y sólo cubre el **Senado**. Para la Cámara no existe ningún equivalente en el portal de datos abiertos.

#### 4b. Estructura del dataset `ucmr-52df` (Senado)

Descubierta via `probe_col2.py`, `probe_col3.py`:

```
Campos: fecha, fullname, proyecto, vote
Rango de fechas: 2017 – 2024
Total registros: ~100 000+ (paginado en bloques de 10 000)
Valores de voto: Si, Sí, No, Abstención, Ausente
```

Cada fila es **un voto de un senador en una votación**; para reconstruir una votación completa se agrupa por `(fecha, proyecto)`.

#### 4c. Búsqueda de rosters de legisladores

| Prueba | Dataset ID | Nombre | Resultado |
|--------|-----------|--------|-----------|
| `probe_col_parties.py` | `sjwx-dr6n` | Directorio de Senadores | ✅ Nombre + partido, cubre 2018-2022 |
| `probe_col_parties2.py` | Búsquedas "senadores 2022", "senado 2022-2026" | — | ❌ No hay dataset actualizado para 2022-2026 |
| `probe_col_parties2.py` | `irbe-p8dy` | Senadores por Partido Político | ✅ Complementario, mismo rango |
| `probe_camara_roster.py` | `5pt5-nxdp` | Representantes 2024-2025 | ✅ Nombre + partido + departamento (columnas mislabelled en la fuente) |
| `probe_camara_roster.py` | `vkjr-c6fe` | Resultados electorales 2018 Cámara | ✅ Útil para cruzar pero no suficiente solo |

---

## Árbol de decisión final

```
¿Existe API o dataset con votaciones nominales?
│
├── Senado
│   ├── datos.gov.co → ucmr-52df  ✅ API SODA estructurada
│   └── senado.gov.co             ❌ Solo PDFs de actas narrativas
│
└── Cámara de Representantes
    ├── datos.gov.co              ❌ No existe dataset de votaciones
    ├── camara.gov.co/votaciones  ❌ JavaScript dinámico sin datos en HTML
    ├── camara.gov.co AJAX        ✅ Índice de sesiones (id + URL de ZIP)
    └── ZIP → PDF                 ✅ Única fuente de votaciones nominales
```

---

## Endpoints y datasets actualmente en uso

### Senado de Colombia

| Propósito | URL | Dataset ID | Notas |
|-----------|-----|-----------|-------|
| Votaciones nominales | `https://www.datos.gov.co/resource/ucmr-52df.json` | `ucmr-52df` | Paginado, 10 000 reg/página. Cada fila = un voto de un senador. Agrupa por `(fecha, proyecto)` → votación |
| Roster senadores (partido) | `https://www.datos.gov.co/resource/sjwx-dr6n.json` | `sjwx-dr6n` | Nombre + partido. Cubre cuatrienios hasta 2022. Sin actualización para 2022-2026 |

### Cámara de Representantes

| Propósito | URL | Notas |
|-----------|-----|-------|
| Nonce CSRF | `https://www.camara.gov.co/secretaria-general/actas-votaciones-y-otros/` | GET. El HTML inline tiene `window.AY_NONCE = "…"`. Caduca con cada deploy del sitio |
| Índice de sesiones plenarias | `https://www.camara.gov.co/wp-admin/admin-ajax.php` | POST. Action: `get_actas_y_otros_page`. Devuelve JSON con `{ items, total_pages }`. ~137 páginas totales |
| ZIP por sesión | `{item.enlace}` (campo en cada item del AJAX) | GET. Contiene PDFs con acta y registro de votación electrónica |
| PDF: votación electrónica | Archivo `registro*votaci*.pdf` dentro del ZIP | Parseado con `pdfplumber`. Texto crudo con secciones `VOTACION N` |
| Roster representantes (partido/dpto) | `https://www.datos.gov.co/resource/5pt5-nxdp.json` | `5pt5-nxdp` | 338 entradas. Columnas con nombres incorrectos en la fuente — el scraper los compensa explícitamente |

---

## Limitaciones conocidas

1. **Nonce efímero (Cámara):** El token `AY_NONCE` se obtiene en cada ejecución del scraper. Si camara.gov.co hace un deploy entre la extracción del nonce y el fetch de sesiones, el nonce puede invalidarse.

2. **PDF con artefactos tipográficos:** Algunas fuentes embebidas en el PDF mapean `í` → `φ` y `ó` → `≤`. Se manejan con regex (`S[φí]` → `AFIRMATIVO`), pero otros artefactos no previstos podrían escapar silenciosamente.

3. **Cámara sin fuente abierta completa:** El dataset `5pt5-nxdp` sólo cubre el periodo 2024-2025. Los ZIPs tienen sesiones desde ~2017 pero el roster para años anteriores no está disponible en datos.gov.co, lo que deja a muchos representantes históricos sin partido asignado.

4. **Senado sin datos post-2024:** El dataset `ucmr-52df` cubre hasta 2024. La última actualización en datos.gov.co es variable; sesiones recientes pueden no haber sido publicadas aún.

5. **`sjwx-dr6n` sin periodo 2022-2026:** El roster de senadores no cubre el cuatrienio vigente al momento de la exploración. Se usan los datos del periodo anterior como aproximación.

6. **congresovisible.uniandes.edu.co:** Esta plataforma académica tiene datos de proyectos de ley y seguimiento legislativo pero **no provee votaciones nominales por legislador** en ningún formato consumible.

---

## Conclusión

La elección de ZIP + PDF para la Cámara no fue una preferencia de diseño sino la consecuencia directa de que **no existe ninguna otra fuente de datos de votaciones nominales para la Cámara de Representantes de Colombia**. El portal de datos abiertos no tiene ese dataset; el sitio oficial entrega los registros sólo como PDFs de sesión. Para el Senado sí se pudo usar la API SODA de datos.gov.co, que es la solución más limpia disponible. El uso de `pdfplumber` para el PDF de Cámara, aunque menos elegante, es robusto en la práctica: el formato interno del PDF ha sido consistente en todas las sesiones probadas (2024-2026).
