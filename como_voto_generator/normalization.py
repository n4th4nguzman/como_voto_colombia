from __future__ import annotations

import json
import re
import unicodedata

from .common import DATA_DIR, log

# ---------------------------------------------------------------------------
# Party classification for law-search breakdown (Colombia)
# ---------------------------------------------------------------------------
# Classifies blocs into the main Colombian parties.
# Return values: PH, LIB, CON, CD, CR, OTROS

_PH_PARTY_KW = [
    "pacto historico",
    "pacto histórico",
    "colombia humana",
    "union patriotica",
    "unión patriótica",
    "polo democratico",
    "polo democrático",
    "marcha patriotica",
    "marcha patriótica",
    "comunes",
    "mais",
    "colombia humana",
    "alianza verde",
    "verde",
]
_LIBERAL_PARTY_KW = [
    "partido liberal",
    "liberal colombiano",
    "p. liberal",
]
_CONSERVADOR_PARTY_KW = [
    "partido conservador",
    "conservador colombiano",
    "colombia conservadora",
    "p. conservador",
]
_CD_PARTY_KW = [
    "centro democratico",
    "centro democrático",
    "c. democratico",
    "c. democrático",
]
_CR_PARTY_KW = [
    "cambio radical",
    "c. radical",
]

# ---------------------------------------------------------------------------
# Bloc -> coalition mapping (for legislator alignment tracking)
# ---------------------------------------------------------------------------
_BLOC_COALITION_MAP: dict[str, str] | None = None

_PACTO_COALITION_KW = [
    "pacto historico",
    "pacto histórico",
    "colombia humana",
    "union patriotica",
    "unión patriótica",
    "polo democratico",
    "polo democrático",
    "comunes",
    "mais",
    "alianza verde",
    "verde",
]
_LIBERAL_COALITION_KW = [
    "partido liberal",
    "liberal colombiano",
]
_CONSERVADOR_COALITION_KW = [
    "partido conservador",
    "conservador colombiano",
    "colombia conservadora",
]
_CD_COALITION_KW = [
    "centro democratico",
    "centro democrático",
]
_CR_COALITION_KW = [
    "cambio radical",
]


def load_bloc_coalition_map() -> dict[str, str]:
    """Load bloc->coalition map from JSON, caching results in memory."""
    global _BLOC_COALITION_MAP
    if _BLOC_COALITION_MAP is not None:
        return _BLOC_COALITION_MAP

    map_path = DATA_DIR / "bloc_coalition_map.json"
    if not map_path.exists():
        log.warning("bloc_coalition_map.json not found - using keyword fallback")
        _BLOC_COALITION_MAP = {}
        return _BLOC_COALITION_MAP

    try:
        with open(map_path, "r", encoding="utf-8") as handle:
            _BLOC_COALITION_MAP = json.load(handle)
    except (json.JSONDecodeError, OSError) as exc:
        log.warning(f"Failed to load bloc_coalition_map.json: {exc}")
        _BLOC_COALITION_MAP = {}
        return _BLOC_COALITION_MAP

    log.info(f"Loaded bloc coalition map with {len(_BLOC_COALITION_MAP)} entries")
    return _BLOC_COALITION_MAP


def _load_bloc_coalition_map() -> dict[str, str]:
    """Backward-compatible alias for callers using the old helper name."""
    return load_bloc_coalition_map()


def _classify_bloc_coalition_fallback(bloc_name: str) -> str:
    """Keyword fallback used when a bloc is missing from the mapping file."""
    name = bloc_name.lower().strip()
    for keyword in _PACTO_COALITION_KW:
        if keyword in name:
            return "PACTO"
    for keyword in _LIBERAL_COALITION_KW:
        if keyword in name:
            return "LIBERAL"
    for keyword in _CONSERVADOR_COALITION_KW:
        if keyword in name:
            return "CONSERVADOR"
    for keyword in _CD_COALITION_KW:
        if keyword in name:
            return "CD"
    for keyword in _CR_COALITION_KW:
        if keyword in name:
            return "CR"
    return "OTROS"


def classify_bloc_mapped(bloc_name: str) -> str:
    """Classify bloc names using the full mapping with keyword fallback."""
    mapping = load_bloc_coalition_map()
    key = bloc_name.lower().strip()
    if key in mapping:
        return mapping[key]
    return _classify_bloc_coalition_fallback(bloc_name)

# Regex helpers for extracting section labels from votación titles
_REF_SUFFIX_RE = re.compile(
    r"\.?(?:PE|CD|JGM|S)-\d+/\d+(?:-[A-Z]+)?[,.]?\s*O\.?\s*D\.?\s*\d+/\d+[,.]?\s*$",
    re.IGNORECASE,
)
_OD_SUFFIX_RE = re.compile(r"[.,]?\s*O\.?\s*D\.?\s*\d+/\d+[,.]?\s*$", re.IGNORECASE)
_OD_PREFIX_RE = re.compile(
    r"^(?:VOTACI[OÓ]N:?\s*)?(?:O\.?\s*D\.?\s*\d+\s*[-–—]\s*)?",
    re.IGNORECASE,
)
_EXP_PREFIX_RE = re.compile(
    r"^(?:EXP(?:EDIENTE)?\.?\s*\S+\s*[-–—]\s*(?:O\.?\s*D\.?\s*\d+\s*[-–—]\s*)?)?",
    re.IGNORECASE,
)
_DICT_RE = re.compile(r"\bDICT\.\s*DE\s*(?:MAY|MIN)\.?\s*", re.IGNORECASE)
_EN_GRAL_RE = re.compile(r"(?:VOT\.?\s*)?EN\s+G(?:ENERAL|RAL)\.?", re.IGNORECASE)
_TITULO_RE = re.compile(r"T[IÍ]TULO\s+([IVXLCDM]+|\d+)", re.IGNORECASE)
_CAPITULO_RE = re.compile(r"CAP[IÍ]?(?:TULO)?[.\s]\s*([IVXLCDM]+|\d+)", re.IGNORECASE)
_ARTICULO_RE = re.compile(
    r"ARTS?[IÍ]?(?:CULOS?)?[.\s°º]\s*(\d+(?:\s*[°º])?)"
    r"(?:\s*(?:AL?|Y|,)\s*(\d+(?:\s*[°º])?))?",
    re.IGNORECASE,
)
_INCISO_RE = re.compile(r"INCISOS?\s+([A-Z](?:\s*(?:AL|Y|,)\s*[A-Z])*)", re.IGNORECASE)


def _clean_votacion_title(title: str) -> str:
    """Elimina ruido de un título de votación para extraer su sección."""
    cleaned = title.strip()
    cleaned = _REF_SUFFIX_RE.sub("", cleaned)
    cleaned = _OD_SUFFIX_RE.sub("", cleaned)
    cleaned = _OD_PREFIX_RE.sub("", cleaned)
    cleaned = _EXP_PREFIX_RE.sub("", cleaned)
    cleaned = re.sub(
        r"^Orden\s+del\s+D[ií]a\s+\d+\s*[-–—.]\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = _DICT_RE.sub("", cleaned)
    return cleaned.strip(" .,")


def extract_section_label(title: str, vtype: str = "") -> str:
    """Extrae una etiqueta descriptiva de sección desde un título de votación."""
    cleaned = _clean_votacion_title(title)

    if _EN_GRAL_RE.search(cleaned) or "EN GENERAL" in vtype.upper():
        return "En General"

    parts: list[str] = []
    for match in _TITULO_RE.finditer(cleaned):
        parts.append(f"Título {match.group(1)}")
    for match in _CAPITULO_RE.finditer(cleaned):
        parts.append(f"Cap. {match.group(1)}")
    for match in _ARTICULO_RE.finditer(cleaned):
        n1 = match.group(1).replace("°", "").replace("º", "").strip()
        if match.group(2):
            n2 = match.group(2).replace("°", "").replace("º", "").strip()
            parts.append(f"Arts. {n1} a {n2}")
        else:
            parts.append(f"Art. {n1}")
    for match in _INCISO_RE.finditer(cleaned):
        parts.append(f"Inc. {match.group(1)}")

    if parts:
        seen: set[str] = set()
        unique: list[str] = []
        for part in parts:
            if part not in seen:
                seen.add(part)
                unique.append(part)
        return ", ".join(unique)

    if re.search(r"en\s+particular", cleaned, re.IGNORECASE):
        return "En Particular"

    vtype_clean = vtype.strip()
    if vtype_clean:
        upper_vtype = vtype_clean.upper()
        if "EN PARTICULAR" in upper_vtype:
            return "En Particular"
        if "EN GENERAL" in upper_vtype:
            return "En General"
        return vtype_clean
    return ""


def classify_bloc_party(bloc_name: str) -> str:
    """Clasifica un bloque en uno de los partidos colombianos principales u OTROS."""
    name = bloc_name.lower().strip()
    for keyword in _PACTO_COALITION_KW:
        if keyword in name:
            return "PH"
    for keyword in _PH_PARTY_KW:
        if keyword in name:
            return "PH"
    for keyword in _LIBERAL_PARTY_KW:
        if keyword in name:
            return "LIB"
    for keyword in _CONSERVADOR_PARTY_KW:
        if keyword in name:
            return "CON"
    for keyword in _CD_PARTY_KW:
        if keyword in name:
            return "CD"
    for keyword in _CR_PARTY_KW:
        if keyword in name:
            return "CR"
    return "OTROS"


# ---------------------------------------------------------------------------
# Department name normalization (Colombia)
# ---------------------------------------------------------------------------
_PROVINCE_CANONICAL: dict[str, str] = {
    "amazonas": "Amazonas",
    "antioquia": "Antioquia",
    "arauca": "Arauca",
    "atlantico": "Atlántico",
    "atlántico": "Atlántico",
    "bogota": "Bogotá D.C.",
    "bogotá": "Bogotá D.C.",
    "bogota d.c.": "Bogotá D.C.",
    "bogotá d.c.": "Bogotá D.C.",
    "bolivar": "Bolívar",
    "bolívar": "Bolívar",
    "boyaca": "Boyacá",
    "boyacá": "Boyacá",
    "caldas": "Caldas",
    "caqueta": "Caquetá",
    "caquetá": "Caquetá",
    "casanare": "Casanare",
    "cauca": "Cauca",
    "cesar": "Cesar",
    "choco": "Chocó",
    "chocó": "Chocó",
    "cordoba": "Córdoba",
    "córdoba": "Córdoba",
    "cundinamarca": "Cundinamarca",
    "guainia": "Guainía",
    "guainía": "Guainía",
    "guaviare": "Guaviare",
    "huila": "Huila",
    "la guajira": "La Guajira",
    "magdalena": "Magdalena",
    "meta": "Meta",
    "narino": "Nariño",
    "nariño": "Nariño",
    "norte de santander": "Norte de Santander",
    "putumayo": "Putumayo",
    "quindio": "Quindío",
    "quindío": "Quindío",
    "risaralda": "Risaralda",
    "san andres y providencia": "San Andrés y Providencia",
    "san andrés y providencia": "San Andrés y Providencia",
    "santander": "Santander",
    "sucre": "Sucre",
    "tolima": "Tolima",
    "valle del cauca": "Valle del Cauca",
    "vaupes": "Vaupés",
    "vaupés": "Vaupés",
    "vichada": "Vichada",
    "circunscripcion especial": "Circunscripción Especial",
    "circunscripción especial": "Circunscripción Especial",
}


def normalize_province(province: str) -> str:
    """Devuelve el nombre canónico de provincia con mayúsculas iniciales."""
    key = unicodedata.normalize("NFC", province.strip().lower())
    return _PROVINCE_CANONICAL.get(key, province.strip())


def normalize_vote(vote_str: str) -> str:
    vote = vote_str.upper().strip()
    if "AFIRMATIV" in vote:
        return "AFIRMATIVO"
    if "NEGATIV" in vote:
        return "NEGATIVO"
    if "ABSTENCI" in vote:
        return "ABSTENCION"
    if "AUSENT" in vote:
        return "AUSENTE"
    if "PRESIDEN" in vote:
        return "PRESIDENTE"
    return vote


def normalize_name(name: str) -> str:
    # Remove nicknames in quotes (e.g., "TOPO", "PIPI")
    normalized = re.sub(r'\s*"[^"]*"', '', name.strip())
    normalized = re.sub(r"\s+", " ", normalized).upper()
    replacements = {
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
        "Ü": "U",
        "Ñ": "N",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return normalized


# ---------------------------------------------------------------------------
# Name alias map: normalized alias -> normalized canonical name.
# ---------------------------------------------------------------------------
NAME_ALIASES: dict[str, str] = {
    "AGUNDEZ, JORGE ALFRESO": "AGUNDEZ, JORGE ALFREDO",
    "LOPEZ, JUAN CARLOS.": "LOPEZ, JUAN CARLOS",
    "AGUIRRE, HILDA": "AGUIRRE, HILDA CLELIA",
    "AVELIN DE GINESTAR, NANCY B.": "AVELIN DE GINESTAR, NANCY",
    "BASUALDO, ROBERTO": "BASUALDO, ROBERTO GUSTAVO",
    "COBOS, JULIO": "COBOS, JULIO CESAR CLETO",
    "CORNEJO, ALFREDO": "CORNEJO, ALFREDO VICTOR",
    "FELLNER, LILIANA": "FELLNER, LILIANA BEATRIZ",
    "FERNANDEZ DE KIRCHNER, CRISTINA E.": "FERNANDEZ DE KIRCHNER, CRISTINA",
    "FILMUS, DANIEL": "FILMUS, DANIEL FERNANDO",
    "GONZALEZ, PABLO G.": "GONZALEZ, PABLO GERARDO",
    "MARQUEZ, NADIA": "MARQUEZ, NADIA JUDITH",
    "MARTINEZ, ALFREDO": "MARTINEZ, ALFREDO ANSELMO",
    "MENEM, EDUARDO": "MENEM, EDUARDO ADRIAN",
    "MIRABELLA, ROBERTO": "MIRABELLA, ROBERTO MARIO",
    "MONTENEGRO, GUILLERMO": "MONTENEGRO, GUILLERMO TRISTAN",
    "PARRILLI, OSCAR ISIDRO": "PARRILLI, OSCAR ISIDRO JOSE",
    "RITONDO, CRISTIAN A.": "RITONDO, CRISTIAN",
    "SANTILLI, DIEGO": "SANTILLI, DIEGO CESAR",
    "SNOPEK, GUILLERMO": "SNOPEK, GUILLERMO EUGENIO MARIO",
    "SORIA, MARTIN": "SORIA, MARTIN IGNACIO",
    "TAIANA, JORGE": "TAIANA, JORGE ENRIQUE",
    "TERRAGNO, RODOLFO": "TERRAGNO, RODOLFO HECTOR",
}
