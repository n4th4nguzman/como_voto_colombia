"""Probe several candidate datasets."""
import requests
import json

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "ComoVoto/1.0"})

def probe(dataset_id, label):
    print(f"\n=== {label} ({dataset_id}) ===")
    # Count
    r = SESSION.get(f"https://www.datos.gov.co/resource/{dataset_id}.json?$select=count(*)%20as%20cnt", timeout=15)
    print("Count:", r.json())
    # Fields
    r2 = SESSION.get(f"https://www.datos.gov.co/resource/{dataset_id}.json?$limit=2", timeout=15)
    data = r2.json()
    if data and isinstance(data, list):
        print("Fields:", list(data[0].keys()))
        print("Row 1:", json.dumps(data[0], ensure_ascii=False)[:300])
    else:
        print("Response:", str(data)[:300])

probe("sjwx-dr6n", "Directorio de Senadores")
probe("irbe-p8dy", "Senadores por Partido Politico")

# Also check if the ucmr-52df has a related dataset (same publisher)
print("\n=== Checking ucmr-52df metadata ===")
r = SESSION.get("https://www.datos.gov.co/api/views/ucmr-52df.json", timeout=15)
if r.ok:
    meta = r.json()
    print("Publisher:", meta.get("owner", {}).get("displayName"))
    print("Category:", meta.get("category"))
    print("Description:", meta.get("description", "")[:300])
    print("Tags:", meta.get("tags", []))
