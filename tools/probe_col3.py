"""Probe the full vote values distribution in Senado dataset."""
import requests

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "ComoVoto/1.0"})

# Get distinct vote values
r = SESSION.get(
    "https://www.datos.gov.co/resource/ucmr-52df.json?$select=vote,%20count(*)%20as%20cnt&$group=vote&$order=cnt%20DESC",
    timeout=15,
)
print("Distinct vote values with counts:", r.json())
print()

# Get date range
r2 = SESSION.get(
    "https://www.datos.gov.co/resource/ucmr-52df.json?$select=min(fecha)%20as%20min_date,%20max(fecha)%20as%20max_date",
    timeout=15,
)
print("Date range:", r2.json())
print()

# Sample recent rows to see all fields
r3 = SESSION.get(
    "https://www.datos.gov.co/resource/ucmr-52df.json?$limit=5&$order=fecha%20DESC",
    timeout=15,
)
import json
for row in r3.json():
    print(json.dumps(row, ensure_ascii=False))
print()

# Count unique proyecto values to understand what a "votacion" looks like
r4 = SESSION.get(
    "https://www.datos.gov.co/resource/ucmr-52df.json?$select=count(distinct%20proyecto)%20as%20uniq_proyectos",
    timeout=15,
)
print("Unique proyectos:", r4.json())
