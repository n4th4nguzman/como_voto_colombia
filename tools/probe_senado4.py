"""Check if Senado plenaria pages have ZIP/PDF files like Camara."""
import requests
from bs4 import BeautifulSoup
import re

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 ComoVoto/1.0",
    "Accept-Language": "es-CO,es;q=0.9",
})

BASE = "http://www.secretariasenado.gov.co"

# Check a plenaria month page
r = SESSION.get(BASE + "/cuatrienio-2022-2026/legislatura-2023-2024/plenarias-3/julio-3", timeout=15)
print(f"Julio plenarias: HTTP {r.status_code}, len={len(r.text)}")
if r.ok:
    soup = BeautifulSoup(r.text, "lxml")
    # Find links to sessions
    sessions = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        text = link.get_text(strip=True)[:60]
        if "julio" in href.lower() or "plenaria" in href.lower() or "acta" in href.lower():
            sessions.append((text, href))
            print(f"  {text!r}: {href[:100]}")
print()

# Also check the cuatrienio 2022-2026 overview for plenarias
r2 = SESSION.get(BASE + "/cuatrienio-2022-2026", timeout=15)
soup2 = BeautifulSoup(r2.text, "lxml")
print("Cuatrienio 2022-2026 links:")
for link in soup2.find_all("a", href=True)[:30]:
    text = link.get_text(strip=True)[:50]
    href = link["href"]
    if "cuatrienio" in href.lower() or "legislat" in href.lower() or "plenaria" in href.lower():
        print(f"  {text!r}: {href[:100]}")
