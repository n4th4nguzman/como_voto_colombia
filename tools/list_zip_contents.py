"""List all files in Camara session ZIPs to find the correct PDF pattern."""
import sys, re
sys.path.insert(0, r"c:\Users\jguzman\Como_voto_colombia")

from como_voto_scraper_colombia.camara_col import (
    _fetch_nonce, _fetch_sessions_page, _download_zip,
)

nonce = _fetch_nonce()
print(f"Nonce: {nonce!r}")

resp = _fetch_sessions_page(nonce, 1)
items = resp.get("data", {}).get("items", [])[:5]
print(f"Sessions: {len(items)}")

for session in items:
    sid = session["id"]
    enlace = session["enlace"]
    titulo = session.get("titulo", "")
    print(f"\nSession {sid}: {titulo}")
    zf = _download_zip(enlace)
    if not zf:
        print("  Could not download ZIP")
        continue
    print("  Files in ZIP:")
    for name in zf.namelist():
        print(f"    {name}")
