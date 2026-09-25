# -*- coding: utf-8 -*-
"""임시 관찰용 — CMP2 엔트리 선두 덤프."""
import sys

from cmp2 import load
from hexdump import dump

path = sys.argv[1]
idxs = [int(x, 0) for x in sys.argv[2:]] or [0]
c = load(path)
for i in idxs:
    d = c.entry(i)
    print("--- %s entry %d (%d bytes) ---" % (c.name, i, len(d)))
    dump(d[:0x60])
