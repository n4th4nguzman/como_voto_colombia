"""Explore the Camara votaciones page to find vote data structure."""
import re
import requests
from bs4 import BeautifulSoup
import json

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 ComoVoto/1.0 (civic project)",
    "Accept-Language": "es-CO,es;q=0.9",
})

# Check datos-abiertos page for any APIs or downloads
r = SESSION.get("https://www.camara.gov.co/secretaria/datos-abiertos", timeout=15)
soup = BeautifulSoup(r.text, "lxml")

# Look for links to APIs or structured data
links = soup.find_all("a", href=True)
interesting = []
for link in links:
    href = link.get("href", "")
    text = link.get_text(strip=True)[:60]
    if any(kw in href.lower() or kw in text.lower() for kw in ["vote", "vot", "api", "json", "csv", "datos", "open"]):
        interesting.append(f"  {text!r}: {href}")

for item in interesting[:20]:
    print(item)
print()

# Check the votaciones page for structured data
r2 = SESSION.get("https://www.camara.gov.co/votaciones", timeout=15)
soup2 = BeautifulSoup(r2.text, "lxml")
# Look for any JSON data embedded in the page 
scripts = soup2.find_all("script", type=False)
for s in scripts[:5]:
    content = s.get_text()
    if "votacion" in content.lower() and len(content) > 50:
        print("Script snippet:", content[:300])
        print()

# Look for forms or endpoints
forms = soup2.find_all("form")
for form in forms[:3]:
    print("Form action:", form.get("action"), "method:", form.get("method"))
    for inp in form.find_all("input"):
        print(f"  Input: name={inp.get('name')} type={inp.get('type')} value={inp.get('value', '')[:30]}")
