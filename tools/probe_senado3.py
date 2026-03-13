"""Check the Secretaria del Senado for voting data."""
import requests
from bs4 import BeautifulSoup
import re

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 ComoVoto/1.0",
    "Accept-Language": "es-CO,es;q=0.9",
})

# The Secretaria del Senado seems promising
url = "http://www.secretariasenado.gov.co"
try:
    r = SESSION.get(url, timeout=15)
    print(f"{url}: HTTP {r.status_code}")
    if r.ok:
        soup = BeautifulSoup(r.text, "lxml")
        t = soup.find("title")
        print(f"  Title: {t.get_text()[:80] if t else 'N/A'}")
        # Find votaciones links
        for link in soup.find_all("a", href=True)[:50]:
            text = link.get_text(strip=True)[:50]
            href = link["href"]
            if any(kw in href.lower() or kw in text.lower() for kw in ["vot", "acta", "sesion", "plenaria"]):
                print(f"  {text!r}: {href[:100]}")
except Exception as e:
    print(f"Error: {e}")
print()

# Try the plenarias page you saw in links
plenarias_url = "http://www.secretariasenado.gov.co/cuatrienio-2022-2026/legislatura-2023-2024/plenarias-3"
try:
    r2 = SESSION.get(plenarias_url, timeout=15)
    print(f"Plenarias page: HTTP {r2.status_code}, len={len(r2.text)}")
    if r2.ok:
        soup2 = BeautifulSoup(r2.text, "lxml")
        t2 = soup2.find("title")
        print(f"Title: {t2.get_text()[:80] if t2 else 'N/A'}")
        # Look for links to vote records
        links = soup2.find_all("a", href=True)
        for link in links[:30]:
            text = link.get_text(strip=True)[:60]
            href = link["href"]
            if text:
                print(f"  {text!r}: {href[:100]}")
except Exception as e:
    print(f"Plenarias error: {e}")
