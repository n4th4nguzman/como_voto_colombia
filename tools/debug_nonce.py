"""Debug nonce extraction from Camara page."""
import sys
import re
sys.path.insert(0, r"c:\Users\jguzman\Como_voto_colombia")
from como_voto_scraper_colombia.core_col import SESSION, PHOTOS_DIR

r = SESSION.get("https://www.camara.gov.co/secretaria-general/actas-votaciones-y-otros/", timeout=15)
print(f"Status: {r.status_code}")

# Try various nonce patterns
patterns = [
    r"""AY_NONCE['"]\s*:\s*['"]([a-f0-9]+)['"]""",
    r"AY_NONCE[^'\"]*['\"]([a-f0-9]+)",
    r"_ajax_nonce[^'\"]*['\"]([a-f0-9]+)",
    r"nonce['\"]:\s*['\"]([a-z0-9]+)['\"]",
    r'"_ajax_nonce"\s*:\s*"([^"]+)"',
    r"AY_NONCE:\"([^\"]+)\"",
    r"AY_NONCE:'([^']+)'",
]
for pat in patterns:
    m = re.search(pat, r.text)
    if m:
        short = repr(pat[:50])
        print(f"Pattern {short} matched: {m.group(1)!r}")
    else:
        short = repr(pat[:50])
        print(f"Pattern {short} NO MATCH")

# Show context around AY_NONCE
idx = r.text.find("AY_NONCE")
if idx >= 0:
    print(f"\nContext:\n{r.text[idx-5:idx+60]!r}")
else:
    print("AY_NONCE not found in page source")
