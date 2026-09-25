# -*- coding: utf-8 -*-
"""CMP2 엔트리 목록 + 간이 지문(선두 바이트, 엔트로피, swap16 SJIS 밀도)."""
import collections
import math
import sys

from cmp2 import SECTOR, load
from swap16_scan import scan


def entropy(b):
    if not b:
        return 0.0
    c = collections.Counter(b)
    n = len(b)
    return -sum(v / n * math.log2(v / n) for v in c.values())


def main(path, limit=None):
    c = load(path)
    print("%s  entries=%d" % (c.name, c.count))
    print("%-4s %-8s %-8s %-10s %-5s %-7s %s" % ("#", "start", "sect", "bytes", "ent", "sjis", "head"))
    for i in range(c.count if limit is None else min(limit, c.count)):
        d = c.entry(i)
        s, e = c.ranges[i]
        sample = d[:0x20000]
        runs = scan(sample, 3)
        nch = sum(r[1] for r in runs)
        head = " ".join("%02X" % x for x in d[:12])
        asc = "".join(chr(x) if 0x20 <= x < 0x7F else "." for x in d[:8])
        print("%-4d %-8d %-8d %-10d %-5.2f %-7d %s |%s|"
              % (i, s, e - s, len(d), entropy(sample[:4096]), nch, head, asc))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
