"""Search broadly for Camara de Representantes vote data on datos.gov.co."""
import requests
import json

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "ComoVoto/1.0"})

# Try common catalog search API patterns
searches = [
    "representantes votaciones",
    "camara representantes votos",
    "congreso votaciones colombia",
    "proyecto ley votacion",
]

for q in searches:
    r = SESSION.get(
        f"https://www.datos.gov.co/api/catalog/v1?q={q.replace(' ', '+')}&limit=8",
        timeout=20,
    )
    if r.ok:
        results = r.json().get("results", [])
        if results:
            print(f"\nSearch '{q}':")
            for item in results[:5]:
                res = item.get("resource", {})
                print(f"  [{res.get('id')}] {res.get('name')} ({res.get('type')})")

# Also try to find a Camara dataset directly
print("\n\n=== Trying known Camara dataset IDs ===")
for did in ["u3jn-rge3", "5t2d-p4s8", "q68v-6cak", "qe3f-mf23", "4tvb-s7bi"]:
    r = SESSION.get(
        f"https://www.datos.gov.co/resource/{did}.json?$limit=1",
        timeout=10,
    )
    if r.ok:
        data = r.json()
        if data and isinstance(data, list) and data:
            print(f"  [{did}] Fields: {list(data[0].keys())[:6]}")
        elif isinstance(data, dict) and data.get("error"):
            pass
        else:
            print(f"  [{did}] Empty or error: {str(data)[:100]}")
    else:
        print(f"  [{did}] HTTP {r.status_code}")
