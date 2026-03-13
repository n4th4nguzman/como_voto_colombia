"""Probe photo sources for Colombian legislators."""
import requests
from bs4 import BeautifulSoup

S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 ComoVoto/1.0", "Accept-Language": "es-CO"})

# --- Camara representantes page ---
r = S.get("https://www.camara.gov.co/representantes", timeout=15)
print("Camara status:", r.status_code, "len:", len(r.text))
soup = BeautifulSoup(r.text, "lxml")
title = soup.find("title")
print("Title:", title.get_text()[:80] if title else "N/A")
imgs = soup.find_all("img", src=True)
print("Total imgs:", len(imgs))
for img in imgs[:15]:
    src = img.get("src", "")
    alt = img.get("alt", "")[:60]
    print("  src=" + src[:90] + "  alt=" + alt)

print()
# Check for any AJAX-loaded content hints
for script in soup.find_all("script"):
    txt = script.get_text()
    if "representant" in txt.lower() and "foto" in txt.lower():
        print("Script with foto hint:", txt[:400])

# Try a direct individual representante page
print("\n--- Individual rep page ---")
r2 = S.get("https://www.camara.gov.co/carolina-arbelaez", timeout=12)
print("Direct page status:", r2.status_code)
if r2.ok:
    soup2 = BeautifulSoup(r2.text, "lxml")
    for img in soup2.find_all("img", src=True)[:8]:
        src = img.get("src", "")
        alt = img.get("alt", "")[:50]
        print("  img:", src[:80], "alt:", alt)
