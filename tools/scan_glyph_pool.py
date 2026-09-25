# -*- coding: utf-8 -*-
"""RAM 전체에서 «32x16 트위들 4bpp 글리프 블록»(256 B)을 전수 탐색.

판정(추측 아님): 글리프는 28x14 이고 칸은 32x16 이므로
열 28~31 과 행 14~15 는 반드시 0 이다. 트위들 y-low 로 되돌린 뒤 이 조건을 본다.
잉크가 너무 적으면(빈 칸) 제외.
"""
import sys

from find_glyph_tex import morton

# 패딩에 해당하는 트위들 인덱스 미리 계산
PAD = []
INK = []
for y in range(16):
    for x in range(32):
        s = morton(x, y, 4, False)
        (PAD if (x >= 28 or y >= 14) else INK).append(s)


def is_glyph(blk):
    for s in PAD:
        b = blk[s >> 1]
        v = (b >> 4) & 0xF if (s & 1) else b & 0xF
        if v:
            return None
    ink = 0
    for s in INK:
        b = blk[s >> 1]
        v = (b >> 4) & 0xF if (s & 1) else b & 0xF
        if v > 3:
            return None
        if v:
            ink += 1
    return ink


def main():
    path = sys.argv[1]
    base = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x8C000000
    step = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x100
    data = open(path, "rb").read()
    hits = []
    for off in range(0, len(data) - 256, step):
        blk = data[off:off + 256]
        if not any(blk):
            continue
        ink = is_glyph(blk)
        if ink and 20 <= ink <= 350:
            hits.append((off, ink))
    print("글리프 블록 후보 %d개 (정렬 0x%X)" % (len(hits), step))
    runs = []
    for off, ink in hits:
        if runs and off == runs[-1][1] + 0x100:
            runs[-1][1] = off
            runs[-1][2] += 1
        else:
            runs.append([off, off, 1])
    runs.sort(key=lambda r: -r[2])
    print("연속 구간 %d개 — 긴 순:" % len(runs))
    for a, b, n in runs[:20]:
        print("   0x%08X ~ 0x%08X  글리프 %d개" % (base + a, base + b + 0x100, n))


if __name__ == "__main__":
    main()
