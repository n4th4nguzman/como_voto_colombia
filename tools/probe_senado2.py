"""Probe the Colombian Senado website for actas/votaciones pages."""
import requests
from bs4 import BeautifulSoup
import re
import json

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 ComoVoto/1.0",
    "Accept-Language": "es-CO,es;q=0.9",
})

# Check Senado main page links for vote/actas sections
r = SESSION.get("https://www.senado.gov.co", timeout=15)
soup = BeautifulSoup(r.text, "lxml")
print("Senado main page links (vote/actas related):")
for link in soup.find_all("a", href=True):
    text = link.get_text(strip=True)[:50]
    href = link["href"]
    if any(kw in href.lower() or kw in text.lower() for kw in ["vot", "acta", "sesion", "plenaria", "datos", "open"]):
        print(f"  {text!r}: {href[:100]}")

print()
# Try the plenaria/actas pages
pages_to_try = [
    "https://www.senado.gov.co/actas-de-plenaria",
    "https://www.senado.gov.co/categoria/plenaria",
    "https://www.senado.gov.co/secretaria/votaciones",
    "https://www.senado.gov.co/actuaciones/votaciones",
    "https://www.senado.gov.co/plenaria",
]
for url in pages_to_try:
    try:
        r2 = SESSION.get(url, timeout=8)
        print(f"{url}: HTTP {r2.status_code}")
        if r2.ok and r2.status_code == 200:
            soup2 = BeautifulSoup(r2.text, "lxml")
            t = soup2.find("title")
            print(f"  Title: {t.get_text()[:60] if t else 'N/A'}")
    except Exception as e:
        print(f"{url}: {str(e)[:60]}")
