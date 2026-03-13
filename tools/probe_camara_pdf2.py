"""Parse all PDFs in Camara ZIP to find vote data."""
import requests
import zipfile
import io
import pdfplumber

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 ComoVoto/1.0",
    "Referer": "https://www.camara.gov.co/",
})

BASE = "https://www.camara.gov.co"
zip_url = BASE + "/wp-content/uploads/2026/02/actas/124586/Asistencias-y-votaciones-26-11-2025.zip"

r = SESSION.get(zip_url, timeout=30)
z = zipfile.ZipFile(io.BytesIO(r.content))

for name in z.namelist():
    if not name.endswith(".pdf"):
        continue
    print(f"\n=== {name} ===")
    pdf_data = z.read(name)
    with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages[:2]):
            print(f"\n  --- Page {i+1} ---")
            # Extract words to see all raw text
            words = page.extract_words()
            if words:
                # Show first 50 words with their positions
                print(f"  First 30 words: {[(w['text'], round(w['x0']), round(w['top'])) for w in words[:30]]}")
            # Try chars
            text = page.extract_text(layout=True)
            if text:
                print(f"  Text layout:\n{text[:800]}")
            # Try tables with different settings
            tables = page.extract_tables({"vertical_strategy": "lines", "horizontal_strategy": "lines"})
            if tables:
                print(f"  Tables (lines): {len(tables)}")
                for t in tables[:2]:
                    print(f"    {t[:5]}")
