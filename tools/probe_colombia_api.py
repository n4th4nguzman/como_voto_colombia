"""Probe datos.gov.co datasets to understand structure for Colombia scrapers."""
import json
import requests

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "ComoVoto-Colombia-Scraper/1.0 (civic project)"})

def probe_dataset(dataset_id: str, label: str):
    url = f"https://www.datos.gov.co/resource/{dataset_id}.json?$limit=3"
    print(f"\n=== {label} ({dataset_id}) ===")
    try:
        r = SESSION.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data:
            print(f"Keys in first row: {list(data[0].keys())}")
            print(f"First row: {json.dumps(data[0], ensure_ascii=False, indent=2)[:800]}")
        else:
            print("Empty response")
    except Exception as e:
        print(f"Error: {e}")

# Known Senado dataset
probe_dataset("ucmr-52df", "Senado votaciones")

# Try to find Camara dataset by probing known IDs from datos.gov.co
# Common Colombian Camara voting datasets
for did in ["w4na-y7b4", "r97q-dra7", "7ghe-6btm"]:
    probe_dataset(did, f"Possible Camara dataset {did}")
