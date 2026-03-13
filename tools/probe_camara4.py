"""Look for any structured Camara voting API endpoint."""
import requests
from bs4 import BeautifulSoup
import re

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 ComoVoto/1.0",
    "Accept-Language": "es-CO,es;q=0.9",
})

# The Camara has a /secretaria-general/actas-votaciones-y-otros/ section
r = SESSION.get("https://www.camara.gov.co/secretaria-general/actas-votaciones-y-otros/", timeout=15)
soup = BeautifulSoup(r.text, "lxml")
print(f"Status: {r.status_code}")
# Find all links to vote-related content
links = soup.find_all("a", href=True)
print("Links to vote-related content:")
for link in links[:40]:
    text = link.get_text(strip=True)[:60]
    href = link["href"]
    if any(kw in href.lower() or kw in text.lower() for kw in ["vot", "acta", "pdf", "sesion"]):
        print(f"  {text!r}: {href[:120]}")
print()

# Check if there's a search/filter mechanism
forms = soup.find_all("form")
print(f"Forms found: {len(forms)}")
for form in forms[:3]:
    print(f"  action={form.get('action')!r} method={form.get('method')!r}")
    for inp in form.find_all(["input", "select"]):
        print(f"    {inp.name} name={inp.get('name')!r} type={inp.get('type')!r}")

# Check for JSON-like data in scripts
for script in soup.find_all("script"):
    c = script.get_text()
    if len(c) > 100 and ("vot" in c.lower() or "acta" in c.lower()):
        print("Script with voting data snippet:", c[:400])
        print()
