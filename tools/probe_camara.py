"""Check the Camara de Representantes website for vote data."""
import requests
from bs4 import BeautifulSoup

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 ComoVoto/1.0 (civic project)",
    "Accept-Language": "es-CO,es;q=0.9",
})

# Try Camara's open data / API pages
urls = [
    "https://www.camara.gov.co/secretaria/datos-abiertos",
    "https://www.camara.gov.co/api/v1/votaciones",
    "https://leyes.camara.gov.co/camara/cliente/htm/home.xhtml",
    "https://www.camara.gov.co/votaciones",
    "https://opendata.camara.gov.co",
]
for url in urls:
    try:
        r = SESSION.get(url, timeout=10)
        print(f"{url}: HTTP {r.status_code}, len={len(r.text)}")
        if r.ok and len(r.text) > 100:
            soup = BeautifulSoup(r.text, "lxml")
            title = soup.find("title")
            print(f"  Title: {title.get_text()[:100] if title else 'N/A'}")
    except Exception as e:
        print(f"{url}: Error - {e}")
