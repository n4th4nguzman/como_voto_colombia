"""Fix double-encoded UTF-8 in index.html.

The file was saved with its UTF-8 bytes interpreted as Windows-1252/Latin-1,
then re-encoded as UTF-8, resulting in garbled Spanish and emoji characters.
This script reverses that process.
"""
from pathlib import Path

# Build CP-1252 reverse map for characters above U+00FF
cp1252_reverse = {}
for byte_val in range(0x80, 0xA0):
    try:
        char = bytes([byte_val]).decode("cp1252")
        if ord(char) > 0xFF:
            cp1252_reverse[char] = byte_val
    except Exception:
        pass  # Undefined in cp1252; fall through to Latin-1


def char_to_byte(char: str) -> int:
    if char in cp1252_reverse:
        return cp1252_reverse[char]
    cp = ord(char)
    if cp <= 0xFF:
        return cp
    raise ValueError(f"Cannot reverse-map: {repr(char)} (U+{cp:04X})")


path = Path(r"c:\Users\jguzman\Como_voto_colombia\docs\index.html")

with open(path, "r", encoding="utf-8-sig") as f:
    content = f.read()

raw = bytes(char_to_byte(c) for c in content)
fixed = raw.decode("utf-8")

with open(path, "w", encoding="utf-8") as f:
    f.write(fixed)

print(f"Done. Wrote {len(fixed)} chars to {path}")
