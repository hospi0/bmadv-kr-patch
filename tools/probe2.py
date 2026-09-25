# -*- coding: utf-8 -*-
"""SYSTEM.DAT 관찰 2 — 5/6 동일성, PAC 하위구조, PVX/PVRT 헤더."""
import hashlib
import struct

from cmp2 import load
from hexdump import dump

c = load(r"..\work\disc1\SYSTEM.DAT")
print("entry5 == entry6 :", hashlib.sha1(c.entry(5)).hexdigest() == hashlib.sha1(c.entry(6)).hexdigest())


def pac_subs(d):
    assert d[:4] == b"PAC "
    n = struct.unpack_from("<I", d, 8)[0]
    total = struct.unpack_from("<I", d, 12)[0]
    offs = list(struct.unpack_from("<%dI" % n, d, 0x20))
    return n, total, offs


for i in (0, 1, 2, 4, 5, 7, 8):
    d = c.entry(i)
    if d[:4] != b"PAC ":
        print("entry %d: magic %r" % (i, d[:4]))
        continue
    n, total, offs = pac_subs(d)
    ends = offs[1:] + [total]
    print("entry %d: PAC n=%d total=0x%X len=0x%X" % (i, n, total, len(d)))
    for j, (o, e) in enumerate(zip(offs, ends)):
        print("    [%2d] off=0x%08X size=0x%-8X magic=%r  %s"
              % (j, o, e - o, d[o:o + 4], " ".join("%02X" % b for b in d[o + 4:o + 0x18])))

print()
print("--- PVX block (entry 2 @0x40) ---")
dump(c.entry(2)[0x40:0x40 + 0x80], 0x40)
