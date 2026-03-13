"""Quick test: scrape only the last 2 Cámara sessions to validate the pipeline."""
import sys
sys.path.insert(0, r"c:\Users\jguzman\Como_voto_colombia")

from como_voto_scraper_colombia.camara_col import (
    _fetch_nonce, _build_camara_roster, _fetch_sessions_page,
    _download_zip, _parse_voting_pdf, _DB_DIR as DATA_DIR,
)
from como_voto_scraper.db import ConsolidatedDB
import re

nonce = _fetch_nonce()
print(f"Nonce: {nonce!r}")
if not nonce:
    print("ERROR: no nonce")
    sys.exit(1)

roster = _build_camara_roster()
print(f"Roster entries: {len(roster)}")

resp = _fetch_sessions_page(nonce, 1)
items = resp.get("data", {}).get("items", [])[:2]
total_pages = resp.get("data", {}).get("total_pages")
print(f"Total pages: {total_pages}, testing {len(items)} sessions")

for session in items:
    sid = session["id"]
    enlace = session["enlace"]
    fecha_iso = session.get("fecha_iso", "")
    if fecha_iso and re.match(r"\d{4}-\d{2}-\d{2}", fecha_iso):
        p = fecha_iso.split("-")
        sdate = f"{p[2]}/{p[1]}/{p[0]}"
    else:
        sdate = fecha_iso
    print(f"\nSession {sid} ({sdate}): {session.get('titulo')}")
    
    zf = _download_zip(enlace)
    if not zf:
        print("  FAILED to download ZIP")
        continue

    pdf_data = None
    for zip_entry in zf.namelist():
        basename = zip_entry.split("/")[-1].lower()
        if (
            basename.endswith(".pdf")
            and "registro" in basename
            and ("votac" in basename or "votaci" in basename)
            and "manual" not in basename
            and "__macosx" not in zip_entry.lower()
        ):
            pdf_data = zf.read(zip_entry)
            print(f"  PDF: {zip_entry}")
            break

    if not pdf_data:
        print("  No voting PDF found")
        continue

    votaciones = _parse_voting_pdf(pdf_data, sid, sdate)
    print(f"  Parsed {len(votaciones)} votaciones")
    for v in votaciones[:3]:
        rows = v.pop("_vote_rows", [])
        print(f"    [{v['id']}] '{v['title'][:60]}' | {v['afirmativo']}Si/{v['negativo']}No/{v['abstencion']}Abst | {len(rows)} votes")
        # Show a few vote rows
        for row in rows[:3]:
            key = re.sub(r"[\s.,]+", "", row["_name"].upper())
            party, dept = roster.get(key, ("?", "?"))
            print(f"      {row['_name']!r} -> {row['vote']} | party={party!r} | dept={dept!r}")
