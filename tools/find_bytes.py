# -*- coding: utf-8 -*-
"""바이트 패턴 검색 (후보 생성용)."""
import sys

path = sys.argv[1]
data = open(path, "rb").read()
for pat in sys.argv[2:]:
    if pat.startswith("hex:"):
        needle = bytes.fromhex(pat[4:])
    else:
        needle = pat.encode("ascii")
    hits = []
    i = data.find(needle)
    while i >= 0 and len(hits) < 200:
        hits.append(i)
        i = data.find(needle, i + 1)
    print("%-28s %d hits: %s" % (pat, len(hits), ", ".join("0x%X" % h for h in hits[:24])))
