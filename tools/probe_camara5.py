"""Probe the Camara WordPress AJAX endpoint for vote data."""
import requests
import json
import re
from bs4 import BeautifulSoup

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 ComoVoto/1.0",
    "Accept-Language": "es-CO,es;q=0.9",
    "Referer": "https://www.camara.gov.co/secretaria-general/actas-votaciones-y-otros/",
})

# Try the AJAX endpoint discovered in the scripts
AJAX_URL = "https://www.camara.gov.co/wp-admin/admin-ajax.php"

# Try known AJAX actions for the Actas pattern
for action in ["get_actas_votaciones", "load_actas", "ap_get_actas", "ay_get_actas"]:
    r = SESSION.post(AJAX_URL, data={
        "action": action,
        "nonce": "11703efb1c",
        "comision": "Secretaría General",
    }, timeout=10)
    print(f"action={action}: HTTP {r.status_code}, len={len(r.text)}, content={r.text[:200]}")
    print()

# Also check: is there an API with a predictable pattern for actas?
# Try a few acta URLs
for year in [2023, 2024, 2025]:
    for acta in [1, 2]:
        url = f"https://www.camara.gov.co/plenaria-acta-{acta:03d}-{year}"
        r = SESSION.get(url, timeout=5)
        if r.status_code == 200:
            print(f"Found: {url}")
            break
