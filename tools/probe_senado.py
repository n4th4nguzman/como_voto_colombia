"""Probe the Colombian Senado website for vote data structure."""
import requests
from bs4 import BeautifulSoup
import re
import json

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 ComoVoto/1.0",
    "Accept-Language": "es-CO,es;q=0.9",
})

# Check the Senado main website
urls = [
    "https://www.senado.gov.co/votaciones",
    "https://www.senado.gov.co/sesiones/actas",
    "https://www.senado.gov.co/index.php/actas-y-votaciones",
]
for url in urls:
    try:
        r = SESSION.get(url, timeout=10)
        print(f"{url}: HTTP {r.status_code}")
        if r.ok:
            soup = BeautifulSoup(r.text, "lxml")
            title = soup.find("title")
            print(f"  Title: {title.get_text()[:80] if title else 'N/A'}")
    except Exception as e:
        print(f"{url}: Error - {str(e)[:80]}")
print()

# Check the Congreso Colombia main portal (a single portal for both)
urls2 = [
    "https://congreso.gov.co",
    "https://leyes.senado.gov.co",
    "https://www.senado.gov.co",
]
for url in urls2:
    try:
        r = SESSION.get(url, timeout=10)
        print(f"{url}: HTTP {r.status_code}, len={len(r.text)}")
        if r.ok:
            soup = BeautifulSoup(r.text, "lxml")
            title = soup.find("title")
            print(f"  Title: {title.get_text()[:80] if title else 'N/A'}")
            # Find API/data links
            for link in soup.find_all("a", href=True)[:5]:
                text = link.get_text(strip=True)[:40]
                print(f"  Link: {text!r}: {link['href'][:80]}")
    except Exception as e:
        print(f"{url}: Error - {str(e)[:80]}")
