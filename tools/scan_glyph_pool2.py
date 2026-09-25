# -*- coding: utf-8 -*-
"""RAM 전체에서 32x16 트위들 4bpp 글리프 블록을 «정렬 무관»으로 전수 탐색.

빠른 선별: 트위들 인덱스상 «두 니블이 모두 패딩»인 바이트는 반드시 0x00 이다.
그 바이트 위치들만 numpy 로 먼저 걸러낸 뒤, 살아남은 후보만 완전 검사한다.
"""
import sys

import numpy as np

from find_glyph_tex import morton

PAD_S, INK_S = set(), set()
for y in range(16):
    for x in range(32):
        s = morton(x, y, 4, False)
        (PAD_S if (x >= 28 or y >= 14) else INK_S).add(s)
# 두 니블이 모두 패딩인 바이트
ZERO_BYTES = sorted(b for b in range(256) if (2 * b) in PAD_S and (2 * b + 1) in PAD_S)
INK_BYTES = sorted(b for b in range(256) if (2 * b) in INK_S and (2 * b + 1) in INK_S)


def full_check(blk):
    for s in PAD_S:
        v = (blk[s >> 1] >> 4) & 0xF if (s & 1) else blk[s >> 1] & 0xF
        if v:
            return None
    ink = 0
    for s in INK_S:
        v = (blk[s >> 1] >> 4) & 0xF if (s & 1) else blk[s >> 1] & 0xF
        if v > 3:
            return None
        if v:
            ink += 1
    return ink


def main():
    path = sys.argv[1]
    base = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x8C000000
    step = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x10
    data = np.frombuffer(open(path, "rb").read(), dtype=np.uint8)
    raw = data.tobytes()
    n = (len(data) - 256) // step
    starts = np.arange(n, dtype=np.int64) * step
    print("패딩 전용 바이트 %d개로 선별 (예: %s)" % (len(ZERO_BYTES), ZERO_BYTES[:8]))
    mask = np.ones(n, dtype=bool)
    for b in ZERO_BYTES[:24]:
        mask &= data[starts + b] == 0
        if mask.sum() < 200000:
            break
    cand = starts[mask]
    print("1차 후보 %d개 → 완전 검사" % len(cand))
    hits = []
    for off in cand:
        o = int(off)
        blk = raw[o:o + 256]
        if not any(blk):
            continue
        ink = full_check(blk)
        if ink and 20 <= ink <= 350:
            hits.append((o, ink))
    print("글리프 블록 %d개" % len(hits))
    runs = []
    for off, ink in hits:
        if runs and off - runs[-1][1] <= 0x100:
            runs[-1][1] = off
            runs[-1][2] += 1
        else:
            runs.append([off, off, 1])
    runs.sort(key=lambda r: -r[2])
    for a, b, c in runs[:25]:
        print("   0x%08X ~ 0x%08X  블록 %d개" % (base + a, base + b + 0x100, c))


if __name__ == "__main__":
    main()
