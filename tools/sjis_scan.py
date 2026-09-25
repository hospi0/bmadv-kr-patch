# -*- coding: utf-8 -*-
"""평문 Shift-JIS 문자열 스캐너 (후보 생성용, 소비자 확정 아님)."""
import sys


def is_sjis_lead(b):
    return 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xEF


def is_sjis_trail(b):
    return 0x40 <= b <= 0x7E or 0x80 <= b <= 0xFC


def scan(data, min_chars=3):
    out = []
    i = 0
    n = len(data)
    while i < n:
        if is_sjis_lead(data[i]) and i + 1 < n and is_sjis_trail(data[i + 1]):
            start = i
            cnt = 0
            while i + 1 < n and is_sjis_lead(data[i]) and is_sjis_trail(data[i + 1]):
                i += 2
                cnt += 1
            if cnt >= min_chars:
                try:
                    s = data[start:i].decode("cp932")
                except UnicodeDecodeError:
                    s = None
                if s:
                    out.append((start, cnt, s))
        else:
            i += 1
    return out


if __name__ == "__main__":
    path = sys.argv[1]
    minc = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    data = open(path, "rb").read()
    res = scan(data, minc)
    print("hits:", len(res), "chars:", sum(r[1] for r in res))
    for off, cnt, s in res[:limit]:
        print("0x%08X %3d  %s" % (off, cnt, s))
