"""Search datos.gov.co for better Colombia congress datasets."""
import requests
import json

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "ComoVoto/1.0"})

# Search the Socrata catalog for Colombian congress vote datasets
print("=== Searching Socrata catalog for voting datasets ===")
r = SESSION.get(
    "https://www.datos.gov.co/api/catalog/v1?q=votaciones+congreso&limit=10",
    timeout=20,
)
if r.ok:
    results = r.json().get("results", [])
    for item in results[:10]:
        print(f"  {item.get('resource', {}).get('id')}: {item.get('resource', {}).get('name')}")
print()

# Also search for camara de representantes votes
r2 = SESSION.get(
    "https://www.datos.gov.co/api/catalog/v1?q=votaciones+camara+representantes&limit=10",
    timeout=20,
)
if r2.ok:
    results2 = r2.json().get("results", [])
    for item in results2[:10]:
        print(f"  {item.get('resource', {}).get('id')}: {item.get('resource', {}).get('name')}")
print()

# Search for senator profiles / partido
r3 = SESSION.get(
    "https://www.datos.gov.co/api/catalog/v1?q=senadores+partido+colombia&limit=10",
    timeout=20,
)
if r3.ok:
    results3 = r3.json().get("results", [])
    for item in results3[:10]:
        res = item.get("resource", {})
        print(f"  {res.get('id')}: {res.get('name')}")
