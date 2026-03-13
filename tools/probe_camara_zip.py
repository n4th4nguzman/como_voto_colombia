"""Download and inspect a Camara session ZIP to understand vote data format."""
import requests
import zipfile
import io
import os

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 ComoVoto/1.0",
    "Referer": "https://www.camara.gov.co/",
})

BASE = "https://www.camara.gov.co"
# Most recent ZIP from previous probe
zip_url = BASE + "/wp-content/uploads/2026/02/actas/124586/Asistencias-y-votaciones-26-11-2025.zip"

print(f"Downloading: {zip_url}")
r = SESSION.get(zip_url, timeout=30)
print(f"Status: {r.status_code}, Content-Type: {r.headers.get('Content-Type')}, Size: {len(r.content)}")

if r.status_code == 200:
    z = zipfile.ZipFile(io.BytesIO(r.content))
    print("\nFiles in ZIP:")
    for info in z.infolist():
        print(f"  {info.filename} ({info.file_size} bytes)")
    print()
    
    # Try to read a couple of files
    for name in z.namelist()[:5]:
        ext = name.lower().rsplit(".", 1)[-1] if "." in name else ""
        print(f"\n--- {name} (ext={ext}) ---")
        if ext == "pdf":
            print("  PDF file - would need pdfplumber to parse")
        elif ext in ("xlsx", "xls"):
            print("  Excel file - would need openpyxl to parse")
            data = z.read(name)
            print(f"  First 50 bytes: {data[:50].hex()}")
        elif ext in ("csv", "txt", "json"):
            data = z.read(name)
            print("  Text content:", data[:500].decode("utf-8", errors="replace"))
        else:
            data = z.read(name)
            print(f"  First 50 bytes ({ext}): {data[:50].hex()}")
