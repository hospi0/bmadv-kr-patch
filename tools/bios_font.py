# -*- coding: utf-8 -*-
"""드림캐스트 bootROM 폰트에서 글리프를 뽑는다.

배치는 japanese-cake/jc-bootrom-font (`font-unpacker.py`) 의 상수를 따랐다:
  0x00100018  폰트 ID 8바이트
  0x00100020  폰트 데이터 시작
    ascii      96 × 36 B (12×24)
    iso-8859-1 96 × 36 B
    jis-x-0201 96 × 36 B
    jis-x-0208 7056 × 72 B (24×24)   ← 한자·가나
    sega-gaij  22 × 72 B
    vmu-icon   129 × 128 B (32×32)

JIS0208 국소 인덱스: row*94 + col.
  row 0..6  → JIS 구 0x21..0x27
  row 7..   → JIS 구 0x30 부터
"""
import sys

DATA = 0x00100020
J0208 = DATA + 288 * 36
GSIZE = 72


def sjis_to_jis(code):
    hi, lo = code >> 8, code & 0xFF
    if lo >= 0x9F:
        j_hi = (hi << 1) - (0x160 if hi >= 0xE0 else 0xE0)
        j_lo = lo - 0x7E
    else:
        j_hi = (hi << 1) - (0x161 if hi >= 0xE0 else 0xE1)
        j_lo = lo - (0x20 if lo >= 0x80 else 0x1F)
    return j_hi, j_lo


def jis_to_local_index(j_hi, j_lo):
    col = j_lo - 0x21
    if 0x21 <= j_hi <= 0x27:
        row = j_hi - 0x21
    else:
        row = (j_hi - 0x30) + 7
    return row * 94 + col


def glyph(rom, code):
    j_hi, j_lo = sjis_to_jis(code)
    n = jis_to_local_index(j_hi, j_lo)
    off = J0208 + n * GSIZE
    data = rom[off:off + GSIZE]
    g = []
    for y in range(24):
        row = []
        for x in range(24):
            bit = y * 24 + x
            row.append(1 if (data[bit >> 3] >> (7 - (bit & 7))) & 1 else 0)
        g.append(row)
    return g, n, off


def art(g, on="##", off=".."):
    return "\n".join("".join(on if v else off for v in row) for row in g)


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    print("폰트 ID:", rom[0x00100018:0x00100020].decode("ascii", "replace"))
    for ch in sys.argv[2]:
        code = int.from_bytes(ch.encode("cp932"), "big")
        g, n, off = glyph(rom, code)
        print("\n=== %s  SJIS 0x%04X  JIS0208 국소인덱스 %d  ROM 0x%06X ===" % (ch, code, n, off))
        print(art(g))
