"""Use discovered AJAX action to fetch Camara actas data."""
import requests
import json

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 ComoVoto/1.0",
    "Accept-Language": "es-CO,es;q=0.9",
    "Referer": "https://www.camara.gov.co/secretaria-general/actas-votaciones-y-otros/",
    "X-Requested-With": "XMLHttpRequest",
})

AJAX_URL = "https://www.camara.gov.co/wp-admin/admin-ajax.php"

# Fetch with the correct action
r = SESSION.post(AJAX_URL, data={
    "action": "get_actas_y_otros_page",
    "_ajax_nonce": "11703efb1c",
    "page": "1",
    "per_page": "5",
    "term": "",
    "tipo": "Votaciones",
    "comision": "Secretaría General",
    "fecha_desde": "",
    "fecha_hasta": "",
}, timeout=15)

print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('Content-Type')}")
print(f"Content: {r.text[:2000]}")
print()

# Also try without tipo filter for broader results
r2 = SESSION.post(AJAX_URL, data={
    "action": "get_actas_y_otros_page",
    "_ajax_nonce": "11703efb1c",
    "page": "1",
    "per_page": "5",
    "term": "",
    "tipo": "All",
    "comision": "Secretaría General",
    "fecha_desde": "",
    "fecha_hasta": "",
}, timeout=15)
print(f"\nAll tipos - Status: {r2.status_code}")
resp = r2.json()
if resp.get("success"):
    items = resp.get("data", {}).get("items", [])
    print(f"Total pages: {resp['data'].get('total_pages')}")
    for item in items[:3]:
        print(json.dumps(item, ensure_ascii=False, indent=2)[:500])
        print()
else:
    print("Error:", r2.text[:500])
