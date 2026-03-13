"""Verify encoding state of index.html."""
import re
from pathlib import Path

path = Path(r"c:\Users\jguzman\Como_voto_colombia\docs\index.html")

with open(path, "rb") as f:
    first = f.read(10)

print("First 10 bytes (hex):", first.hex())
print("Has UTF-8 BOM:", first[:3] == bytes([0xEF, 0xBB, 0xBF]))

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

title_m = re.search(r"<title>(.+?)</title>", content)
ranking_m = re.search(r"Ranking de mandatos[^<]+", content)
logo_m = re.search(r'logo-icon">([^<]+)<', content)

print("Title:", title_m.group(1) if title_m else "NOT FOUND")
print("Ranking:", ranking_m.group(0) if ranking_m else "NOT FOUND")
print("Logo icon:", repr(logo_m.group(1)) if logo_m else "NOT FOUND")

# Check for any double-encoded patterns (Ã should not appear)
garbled = len(re.findall(r"[ÃÂ]{2}", content))
print(f"Garbled char pairs (should be 0): {garbled}")
