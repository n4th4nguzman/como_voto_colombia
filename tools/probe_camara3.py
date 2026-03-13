"""Explore the Camara votaciones page more deeply."""
import re
import requests
from bs4 import BeautifulSoup
import json

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 ComoVoto/1.0 (civic project)",
    "Accept-Language": "es-CO,es;q=0.9",
})

# Check the transparency datos abiertos section
r = SESSION.get("https://www.camara.gov.co/transparencia/datos-abiertos/seccion-de-datos-abiertos/", timeout=15)
soup = BeautifulSoup(r.text, "lxml")
print(f"Status: {r.status_code}")
# Find all links
for link in soup.find_all("a", href=True)[:30]:
    text = link.get_text(strip=True)[:60]
    href = link["href"]
    if text:
        print(f"  {text!r}: {href[:120]}")
print()
print("---")
# Also check the actual votaciones page more carefully
r2 = SESSION.get("https://www.camara.gov.co/votaciones", timeout=15)
soup2 = BeautifulSoup(r2.text, "lxml")
# Find voting records or tables
tables = soup2.find_all("table")
print(f"Tables found on votaciones page: {len(tables)}")
if tables:
    for t in tables[:2]:
        headers = [th.get_text(strip=True) for th in t.find_all("th")]
        print("  Table headers:", headers)
        rows = t.find_all("tr")[1:3]
        for row in rows:
            cells = [td.get_text(strip=True)[:40] for td in row.find_all("td")]
            print("  Row:", cells)

# Find pagination or year links
year_links = soup2.find_all("a", href=re.compile(r"\d{4}"))
print(f"\nYear links: {len(year_links)}")
for link in year_links[:5]:
    print(f"  {link.get_text(strip=True)!r}: {link['href'][:100]}")
