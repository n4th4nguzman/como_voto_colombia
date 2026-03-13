"""Probe column metadata of the Senado datos.gov.co dataset."""
import requests
import json

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "ComoVoto/1.0"})

# Get distinct vote values
r = SESSION.get(
    "https://www.datos.gov.co/resource/ucmr-52df.json?$limit=50&$order=fecha%20DESC",
    timeout=15,
)
data = r.json()
votes = sorted({row.get("vote", "") for row in data})
print("Vote values found:", votes)
print()
print("All fields in rows:", sorted(data[0].keys()) if data else "none")
print()

# Get metadata
r2 = SESSION.get("https://www.datos.gov.co/api/views/ucmr-52df.json", timeout=15)
if r2.ok:
    meta = r2.json()
    cols = meta.get("columns", [])
    print("All columns in dataset:")
    for col in cols:
        fn = col.get("fieldName", "")
        dt = col.get("dataTypeName", "")
        nm = col.get("name", "")
        print(f"  {fn!r} ({dt}): {nm}")

# How many total rows?
r3 = SESSION.get(
    "https://www.datos.gov.co/resource/ucmr-52df.json?$select=count(*)%20as%20cnt",
    timeout=15,
)
print()
print("Total row count:", r3.json())
