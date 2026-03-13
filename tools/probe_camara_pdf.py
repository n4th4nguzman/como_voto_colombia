"""Parse the Camara electronic voting PDF to understand structure."""
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
    if "votacion" in name.lower() and name.endswith(".pdf"):
        print(f"=== Parsing: {name} ===")
        pdf_data = z.read(name)
        with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
            print(f"Total pages: {len(pdf.pages)}")
            # Show first 3 pages
            for i, page in enumerate(pdf.pages[:3]):
                print(f"\n--- Page {i+1} ---")
                # Try to extract tables
                tables = page.extract_tables()
                if tables:
                    for j, table in enumerate(tables):
                        print(f"  Table {j+1} ({len(table)} rows):")
                        for row in table[:8]:
                            print(f"    {row}")
                # Try raw text
                text = page.extract_text()
                if text and not tables:
                    print("  Text:", text[:600])
        break
