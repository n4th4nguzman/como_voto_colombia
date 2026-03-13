from __future__ import annotations

import io
import re
import time
import unicodedata
import zipfile
from collections import defaultdict

import pdfplumber

from pathlib import Path as _Path
from .core_col import REQUEST_DELAY, SESSION, log

# ConsolidatedDB files live in data/ root (not data/colombia/)
_DB_DIR = _Path(__file__).resolve().parent.parent / "data"
_DB_DIR.mkdir(parents=True, exist_ok=True)

try:
    from como_voto_scraper.db import ConsolidatedDB
except ImportError:
    from scraper import ConsolidatedDB  # type: ignore

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CAMARA_BASE = "https://www.camara.gov.co"
AJAX_URL = f"{CAMARA_BASE}/wp-admin/admin-ajax.php"
ACTAS_PAGE = f"{CAMARA_BASE}/secretaria-general/actas-votaciones-y-otros/"

SODA_BASE = "https://www.datos.gov.co/resource"
ROSTER_DATASET = "5pt5-nxdp"  # Camara representatives 2024-2025: name, dept, party

SESSIONS_PER_PAGE = 10

# Procedural / quorum votes we skip (not real legislative votes)
# The PDF strips spaces so "SESIÓN FORMAL" appears as "SESIÓNFORMAL" or "SESIONFORMA"
_SKIP_KEYWORDS = re.compile(
    r"quorum|sesi[oóO≤]n?\s*formal|sesi[oO≤][^a-zA-Z]*form|sesionform|formales|receso",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _norm_key(name: str) -> str:
    """Uppercase ASCII without spaces/punctuation — for cross-source matching."""
    nfkd = unicodedata.normalize("NFKD", name.upper())
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[\s.,]+", "", ascii_str)


def _fetch_nonce() -> str:
    """Extract the WordPress AJAX nonce from the actas page."""
    try:
        r = SESSION.get(ACTAS_PAGE, timeout=15)
        r.raise_for_status()
        m = re.search(r'AY_NONCE["\']?\s*:\s*["\']([a-f0-9]+)["\']', r.text)
        if m:
            return m.group(1)
    except Exception as exc:
        log.warning(f"Could not fetch nonce: {exc}")
    return ""


def _build_camara_roster() -> dict[str, tuple[str, str]]:
    """Return norm_key → (party, department) from datos.gov.co dataset 5pt5-nxdp."""
    log.info("Loading Cámara roster from 5pt5-nxdp...")
    try:
        r = SESSION.get(f"{SODA_BASE}/{ROSTER_DATASET}.json?$limit=300", timeout=15)
        r.raise_for_status()
        rows = r.json()
    except Exception as exc:
        log.warning(f"Could not fetch Cámara roster: {exc}")
        return {}

    roster: dict[str, tuple[str, str]] = {}
    for row in rows:
        # The dataset columns are mislabelled:
        # "_" = full name  |  "apelidos_y_nombre" = department  |  "partido_o_movimiento" = party
        name = row.get("_", "").strip()
        dept = row.get("apelidos_y_nombre", "").strip()
        party = row.get("partido_o_movimiento", "").strip()
        if not name:
            continue
        key = _norm_key(name)
        roster[key] = (party, dept)
        # Also store with name components reversed (apellidos+nombres vs nombres+apellidos)
        parts = name.split()
        if len(parts) >= 4:
            reversed_name = " ".join(parts[2:] + parts[:2])
            roster[_norm_key(reversed_name)] = (party, dept)
    log.info(f"Loaded {len(roster)} Cámara roster entries")
    return roster


def _fetch_sessions_page(nonce: str, page: int) -> dict:
    """Fetch one page of plenaria sessions from the Cámara AJAX endpoint."""
    time.sleep(REQUEST_DELAY)
    try:
        r = SESSION.post(
            AJAX_URL,
            data={
                "action": "get_actas_y_otros_page",
                "_ajax_nonce": nonce,
                "page": str(page),
                "per_page": str(SESSIONS_PER_PAGE),
                "term": "",
                "tipo": "Sesiones Plenarias",
                "comision": "Secretaría General",
                "fecha_desde": "",
                "fecha_hasta": "",
            },
            headers={"Referer": ACTAS_PAGE, "X-Requested-With": "XMLHttpRequest"},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        log.warning(f"AJAX error on page {page}: {exc}")
        return {}


def _download_zip(enlace: str) -> zipfile.ZipFile | None:
    """Download a session ZIP file and return the ZipFile object."""
    url = enlace if enlace.startswith("http") else f"{CAMARA_BASE}{enlace}"
    time.sleep(REQUEST_DELAY)
    try:
        r = SESSION.get(url, timeout=60)
        r.raise_for_status()
        return zipfile.ZipFile(io.BytesIO(r.content))
    except Exception as exc:
        log.warning(f"Could not download ZIP {url}: {exc}")
        return None


def _norm_vote_pdf(raw: str) -> str:
    """Map PDF vote text to canonical AFIRMATIVO / NEGATIVO / ABSTENCION."""
    # In some PDF fonts Sí renders as Sφ; ó/ó → ≤; etc.
    s = raw.strip()
    if re.match(r"^S[φí]$", s, re.IGNORECASE) or s.lower() in ("si", "sí"):
        return "AFIRMATIVO"
    if s.lower() == "no":
        return "NEGATIVO"
    if re.search(r"abstenci", s, re.IGNORECASE):
        return "ABSTENCION"
    # Fallback: treat anything starting with S as affirmative
    if s.upper().startswith("S"):
        return "AFIRMATIVO"
    return "NEGATIVO"


def _parse_voting_pdf(pdf_data: bytes, session_id: str, session_date: str) -> list[dict]:
    """Parse the 'Registro asistencia y votacion Electrónica' PDF.

    Returns a list of raw votación dicts ready for db.add_votacion().
    """
    try:
        with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
            full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as exc:
        log.warning(f"PDF parse error (session {session_id}): {exc}")
        return []

    # ----------------------------------------------------------------
    # 1. Extract attendance list (legislators present in this session)
    # ----------------------------------------------------------------
    # Attendees are listed before the first VOTACION block.
    pre_vote_text = re.split(r"\nVOTACION\s+1\b", full_text, maxsplit=1)[0]
    attendance: set[str] = set()
    for line in pre_vote_text.split("\n"):
        # Lines: "1. APELLIDONOMBRECONCATENADO  2025-11-26 11:37:40"
        m = re.match(r"^\s*\d+\.\s+([A-ZÁÉÍÓÚÑa-záéíóúñ][A-ZÁÉÍÓÚÑa-záéíóúñ]{4,})\s", line)
        if m:
            attendance.add(m.group(1).strip())

    # ----------------------------------------------------------------
    # 2. Split into individual VOTACION blocks
    # ----------------------------------------------------------------
    # re.split with a capturing group keeps the separator values
    parts = re.split(r"\nVOTACION\s+(\d+)\n", full_text)
    # parts = [preamble, "1", block1, "2", block2, ...]

    votaciones: list[dict] = []
    i = 1
    while i < len(parts) - 1:
        vot_num = parts[i].strip()
        block = parts[i + 1]
        i += 2

        # -- Title --
        title_m = re.search(
            r"Nombredelavotaci[^:]*:?(.+?)(?:Iniciodela|Resultados)",
            block,
            re.DOTALL,
        )
        title = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else ""

        # Skip quorum / procedural votes
        if _SKIP_KEYWORDS.search(title):
            continue
        if not title:
            continue

        # -- Date + time --
        time_m = re.search(
            r"Iniciodelavotaci[^:]*:?(\d{4}-\d{2}-\d{2})(\d{2}:\d{2}:\d{2})",
            block,
        )
        if time_m:
            ymd = time_m.group(1).split("-")
            vot_date = f"{ymd[2]}/{ymd[1]}/{ymd[0]} - {time_m.group(2)[:5]}"
        else:
            vot_date = session_date

        # -- Per-legislator votes --
        # Line pattern: "N. NAMECONCATENATED Sφ" or "N. NAMECONCATENATED No"
        vote_lines: list[tuple[str, str]] = []
        for line in block.split("\n"):
            # The name may or may not have internal spaces (PDF encoding artifact)
            m2 = re.match(
                r"^\s*\d+\.\s+([A-ZÁÉÍÓÚÑa-záéíóúñ][\w]+)\s+(S[φí]|Si|No|Abstenci[oó≤]n?)\s*$",
                line,
                re.IGNORECASE,
            )
            if m2:
                vote_lines.append((m2.group(1).strip(), m2.group(2).strip()))

        if not vote_lines:
            continue

        # -- Compute totals --
        voted_names: set[str] = set()
        afirm = negat = abst = ausente = 0
        vote_rows: list[dict] = []

        for leg_name, vote_raw in vote_lines:
            voted_names.add(leg_name)
            vote_norm = _norm_vote_pdf(vote_raw)
            vote_rows.append({"_name": leg_name, "vote": vote_norm})
            if vote_norm == "AFIRMATIVO":
                afirm += 1
            elif vote_norm == "NEGATIVO":
                negat += 1
            else:
                abst += 1

        # Legislators present but who didn't cast a vote → ABSTENCION
        for absent_name in attendance - voted_names:
            vote_rows.append({"_name": absent_name, "vote": "ABSTENCION"})
            abst += 1

        result = "APROBADO" if afirm > negat else "RECHAZADO"

        votaciones.append({
            "id": f"{session_id}_{vot_num}",
            "title": title[:300],
            "date": vot_date,
            "result": result,
            "afirmativo": afirm,
            "negativo": negat,
            "abstencion": abst,
            "ausente": ausente,
            "_vote_rows": vote_rows,
        })

    return votaciones


# ---------------------------------------------------------------------------
# Main scraper
# ---------------------------------------------------------------------------

def scrape_camara_colombia() -> None:
    """Scrape Cámara de Representantes Colombia voting data.

    Sessions are fetched via the Cámara's WordPress AJAX API; each session
    ZIP contains a PDF with the electronic roll-call votes which is parsed
    by pdfplumber.  Data is written to data/camara_col.json.
    """
    log.info("=== Scraping Colombian Cámara de Representantes data ===")

    db_path = _DB_DIR / "camara_col.json"
    db = ConsolidatedDB(db_path)
    db.load()
    existing_ids: set[str] = set(db._votacion_ids)
    log.info(f"Existing DB: {len(db.votaciones)} votaciones")

    roster = _build_camara_roster()

    nonce = _fetch_nonce()
    if not nonce:
        log.error("Could not obtain AJAX nonce — aborting Cámara scrape.")
        return
    log.info(f"Nonce obtained: {nonce}")

    page = 1
    total_pages: int | None = None
    new_count = 0

    while total_pages is None or page <= total_pages:
        log.info(f"Fetching sessions page {page}/{total_pages or '?'}...")
        resp = _fetch_sessions_page(nonce, page)

        if not resp.get("success"):
            log.warning(f"AJAX non-success on page {page}")
            break

        payload = resp.get("data", {})
        items = payload.get("items", [])
        total_pages = payload.get("total_pages", page)

        if not items:
            break

        for session in items:
            session_id = session.get("id", "")
            enlace = session.get("enlace", "")
            fecha_iso = session.get("fecha_iso", "")
            titulo = session.get("titulo", "")

            if not session_id or not enlace:
                continue

            # Already processed if any child votacion from this session exists
            if f"{session_id}_1" in existing_ids:
                log.debug(f"  Skip (already done): session {session_id}")
                continue

            # Convert fecha_iso (YYYY-MM-DD) to DD/MM/YYYY
            if fecha_iso and re.match(r"\d{4}-\d{2}-\d{2}", fecha_iso):
                p = fecha_iso.split("-")
                session_date = f"{p[2]}/{p[1]}/{p[0]}"
            else:
                session_date = fecha_iso

            log.info(f"  Session {session_id}: {titulo}")

            zf = _download_zip(enlace)
            if zf is None:
                continue

            # Find the electronic voting PDF by basename (not folder name)
            pdf_data: bytes | None = None
            for zip_entry in zf.namelist():
                basename = zip_entry.split("/")[-1].lower()
                if (
                    basename.endswith(".pdf")
                    and "registro" in basename
                    and ("votac" in basename or "votaci" in basename)
                    and "manual" not in basename
                    and "__macosx" not in zip_entry.lower()
                ):
                    pdf_data = zf.read(zip_entry)
                    break

            if pdf_data is None:
                log.warning(f"  No electronic voting PDF in session {session_id}")
                continue

            votaciones = _parse_voting_pdf(pdf_data, session_id, session_date)
            log.info(f"  Parsed {len(votaciones)} votaciones from session {session_id}")

            for vot in votaciones:
                if vot["id"] in existing_ids:
                    continue

                # Attach party + province from roster
                votes: list[dict] = []
                for row in vot.pop("_vote_rows", []):
                    leg_name: str = row["_name"]
                    party, dept = roster.get(_norm_key(leg_name), ("", ""))
                    votes.append({
                        "name": leg_name,
                        "bloc": party,
                        "province": dept,
                        "vote": row["vote"],
                    })

                db.add_votacion({
                    "id": vot["id"],
                    "chamber": "camara_col",
                    "url": enlace,
                    "title": vot["title"],
                    "date": vot["date"],
                    "result": vot["result"],
                    "type": "EN GENERAL",
                    "period": "",
                    "afirmativo": vot["afirmativo"],
                    "negativo": vot["negativo"],
                    "abstencion": vot["abstencion"],
                    "ausente": vot["ausente"],
                    "votes": votes,
                })
                existing_ids.add(vot["id"])
                new_count += 1

        page += 1

    db.save()
    log.info(f"Cámara: +{new_count} votaciones (total: {len(db.votaciones)})")


if __name__ == "__main__":
    scrape_camara_colombia()