"""Check for 2022-2026 senator roster and camara representative details."""
import requests
import json

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "ComoVoto/1.0"})

# Check all sjwx-dr6n data for distinct periods
r = SESSION.get(
    "https://www.datos.gov.co/resource/sjwx-dr6n.json?$select=periodo,%20count(*)%20as%20cnt&$group=periodo",
    timeout=15,
)
print("Senator dataset periods:", r.json())

# Search for 2022-2026 senators dataset
for search_term in ["senadores%202022", "senado%202022-2026", "senadores%20partido%202022"]:
    r2 = SESSION.get(
        f"https://www.datos.gov.co/api/catalog/v1?q={search_term}&limit=5",
        timeout=15,
    )
    if r2.ok:
        results = r2.json().get("results", [])
        if results:
            print(f"\nSearch '{search_term}':")
            for item in results[:3]:
                res = item.get("resource", {})
                print(f"  [{res.get('id')}] {res.get('name')}")

# Check the camara 2024-2025 dataset more carefully
print("\n=== Camara 2024-2025 dataset (all entries) ===")
r3 = SESSION.get(
    "https://www.datos.gov.co/resource/5pt5-nxdp.json?$limit=10&$order=_",
    timeout=15,
)
for row in r3.json()[:5]:
    print(json.dumps(row, ensure_ascii=False)[:300])

# Get field names
print("\nField names:", list(r3.json()[0].keys()) if r3.json() else "N/A")
