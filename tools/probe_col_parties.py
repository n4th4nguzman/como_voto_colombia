"""Check senator party data and look for a Camara representatives roster."""
import requests
import json

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "ComoVoto/1.0"})

# Get all senators with party info
print("=== Senators with party (sjwx-dr6n) ===")
r = SESSION.get(
    "https://www.datos.gov.co/resource/sjwx-dr6n.json?$limit=200&$order=periodo%20DESC",
    timeout=15,
)
data = r.json()
print(f"Total: {len(data)}")
for row in data[:5]:
    print(json.dumps(row, ensure_ascii=False)[:200])
print()
# Get distinct periods
periods = sorted({row.get("periodo", "") for row in data}, reverse=True)
print("Periods:", periods[:5])

# Check count endpoint
r2 = SESSION.get(
    "https://www.datos.gov.co/resource/sjwx-dr6n.json?$select=count(*)%20as%20cnt",
    timeout=15,
)
print("Count:", r2.json())

# Also search datos.gov.co for camara de representantes roster
print("\n=== Searching for Camara roster on datos.gov.co ===")
r3 = SESSION.get(
    "https://www.datos.gov.co/api/catalog/v1?q=representantes+camara+partido&limit=10",
    timeout=15,
)
if r3.ok:
    results = r3.json().get("results", [])
    for item in results[:5]:
        res = item.get("resource", {})
        print(f"  [{res.get('id')}] {res.get('name')} (type={res.get('type')})")
