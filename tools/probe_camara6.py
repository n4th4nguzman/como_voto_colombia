"""Extract the full AJAX call JS from the Camara actas page."""
import requests
import re

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 ComoVoto/1.0",
    "Accept-Language": "es-CO,es;q=0.9",
})

r = SESSION.get("https://www.camara.gov.co/secretaria-general/actas-votaciones-y-otros/", timeout=15)

# Find the big inline script with window.AP_CFG
scripts = re.findall(r"<script[^>]*>(.*?)</script>", r.text, re.DOTALL)
for s in scripts:
    if "AP_CFG" in s or "AY_NONCE" in s or "ay_" in s.lower():
        print("=== Found matching script ===")
        print(s[:3000])
        print()
