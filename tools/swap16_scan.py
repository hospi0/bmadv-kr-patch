# -*- coding: utf-8 -*-
"""swap16 저장 SJIS 스캐너.

관측(후보): SCENARIO.DAT 는 u16 LE 워드 스트림이고, 텍스트 문자는
SJIS 2바이트를 u16 LE 로 담아 디스크에서는 바이트가 뒤집혀 보인다.
따라서 워드 w = LE16(data[i:i+2]) 를 big-endian 2바이트로 되돌려 cp932 로 읽는다.
제어 토큰은 w < 0x8140 인 작은 값들로 보인다.
"""
import struct
import sys


def words(data):
    n = len(data) // 2
    return struct.unpack("<%dH" % n, data[:n * 2])


def is_sjis_word(w):
    hi, lo = w >> 8, w & 0xFF
    if not (0x81 <= hi <= 0x9F or 0xE0 <= hi <= 0xEF):
        return False
    if not (0x40 <= lo <= 0x7E or 0x80 <= lo <= 0xFC):
        return False
    return True


def scan(data, min_chars=2):
    ws = words(data)
    out = []
    i = 0
    n = len(ws)
    while i < n:
        if is_sjis_word(ws[i]):
            start = i
            while i < n and is_sjis_word(ws[i]):
                i += 1
            if i - start >= min_chars:
                raw = b"".join(struct.pack(">H", w) for w in ws[start:i])
                try:
                    s = raw.decode("cp932")
                except UnicodeDecodeError:
                    s = raw.decode("cp932", "replace")
                out.append((start * 2, i - start, s))
        else:
            i += 1
    return out


if __name__ == "__main__":
    path = sys.argv[1]
    minc = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    data = open(path, "rb").read()
    res = scan(data, minc)
    print("file:", path, "size:", len(data))
    print("runs:", len(res), "chars:", sum(r[1] for r in res))
    for off, cnt, s in res[:limit]:
        print("0x%08X %3d  %s" % (off, cnt, s))
