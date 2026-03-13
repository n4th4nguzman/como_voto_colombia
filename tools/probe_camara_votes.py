"""Parse all pages of the voting PDF to find the actual vote data section."""
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

# Focus on the electronic voting PDF
for name in z.namelist():
    if "votacion" in name.lower() and "electr" in name.lower() and name.endswith(".pdf"):
        pdf_data = z.read(name)
        with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
            print(f"Total pages: {len(pdf.pages)}")
            # Read all pages to find vote result sections
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                # Look for pages with vote results (SI/NO patterns)
                if any(kw in text.upper() for kw in ["SI ", "NO ", "AFIRMATIVO", "NEGATIVO", "VOTACION", "VOTO"]):
                    print(f"\n=== Page {i+1} (has vote keywords) ===")
                    print(text[:1000])
                    # Also try tables
                    tables = page.extract_tables()
                    if tables:
                        print(f"Tables: {len(tables)}")
                        for t in tables[:2]:
                            for row in t[:5]:
                                print(f"  {row}")
