"""Check the Camara representatives roster dataset."""
import requests
import json

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "ComoVoto/1.0"})

# Check the representatives 2024-2025 dataset
print("=== REPRESENTANTES PERIODO 2024-2025 (5pt5-nxdp) ===")
r = SESSION.get(
    "https://www.datos.gov.co/resource/5pt5-nxdp.json?$limit=5",
    timeout=15,
)
data = r.json()
if data and isinstance(data, list):
    print("Fields:", list(data[0].keys()) if data else [])
    for row in data[:3]:
        print(json.dumps(row, ensure_ascii=False)[:300])
else:
    print("Response:", str(data)[:300])

r2 = SESSION.get(
    "https://www.datos.gov.co/resource/5pt5-nxdp.json?$select=count(*)%20as%20cnt",
    timeout=15,
)
print("\nCount:", r2.json())

# Also check the 2018 dataset
print("\n=== RESULTADOS ELECTORALES 2018 CAMARA (vkjr-c6fe) ===")
r3 = SESSION.get(
    "https://www.datos.gov.co/resource/vkjr-c6fe.json?$limit=3",
    timeout=15,
)
data3 = r3.json()
if data3 and isinstance(data3, list) and data3:
    print("Fields:", list(data3[0].keys()))
    print("Row:", json.dumps(data3[0], ensure_ascii=False)[:300])
