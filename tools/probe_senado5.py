"""Check a specific Senado plenaria day for vote data files."""
import requests
from bs4 import BeautifulSoup
import re

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 ComoVoto/1.0",
    "Accept-Language": "es-CO,es;q=0.9",
})

BASE = "http://www.secretariasenado.gov.co"

r = SESSION.get(BASE + "/cuatrienio-2022-2026/legislatura-2023-2024/plenarias-3/julio-3/jueves-20-de-julio-de-2023", timeout=15)
print(f"Status: {r.status_code}, len={len(r.text)}")
if r.ok:
    soup = BeautifulSoup(r.text, "lxml")
    # Find all file/download links
    print("Files/downloads on this plenaria day page:")
    for link in soup.find_all("a", href=True):
        href = link["href"]
        text = link.get_text(strip=True)[:80]
        if any(ext in href.lower() for ext in [".pdf", ".zip", ".xlsx", ".xls", ".doc"]):
            print(f"  {text!r}: {href[:120]}")
    
    # Check for images or iframes that might show vote data
    for img in soup.find_all(["img", "iframe", "embed"])[:5]:
        print(f"  Media: {img.get('src', '')[:80]}")
    
    # Show text content
    content = soup.find("div", class_=re.compile("content|main|article|post", re.I))
    if content:
        print("\nPage content (truncated):")
        print(content.get_text()[:600])
