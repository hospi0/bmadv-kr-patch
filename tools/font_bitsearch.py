# -*- coding: utf-8 -*-
"""비트 오프셋·행 간격 무관 글리프 검색.

바이트 정렬을 가정하지 않는다. 글리프의 «가장 선택적인 행»(긴 연속 잉크)을
비트 단위로 찾고, 나머지 행이 일정한 비트 간격(stride)으로 따라오는지 본다.

두 극성(1=잉크 / 0=잉크)을 모두 본다.
"""
import sys

import numpy as np

from glyph_extract import glyphs


def rows_mask(g):
    return [[1 if v else 0 for v in row] for row in g]


def best_anchor(rows):
    """가장 긴 연속 잉크를 가진 행 index 와 그 길이."""
    best = (0, 0, 0)  # (길이, 행, 시작)
    for i, r in enumerate(rows):
        run = start = 0
        for x, v in enumerate(r):
            if v:
                if run == 0:
                    start = x
                run += 1
                if run > best[0]:
                    best = (run, i, start)
            else:
                run = 0
    return best


def find_runs(bits, n):
    """길이 n 이상의 연속 1 비트 시작 위치들 (양쪽이 0으로 막힌 것만)."""
    d = np.diff(np.concatenate(([0], bits, [0])).astype(np.int8))
    starts = np.where(d == 1)[0]
    ends = np.where(d == -1)[0]
    lens = ends - starts
    sel = lens == n
    return starts[sel]


def main():
    state, off, w, h, gi = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    tgt, base = sys.argv[6], int(sys.argv[7], 0) if len(sys.argv) > 7 else 0
    g = glyphs(open(state, "rb").read(), off, w, h)[gi][1]
    rows = rows_mask(g)
    runlen, ri, rs = best_anchor(rows)
    print("앵커: 행 %d, 시작 x=%d, 연속 잉크 %d px" % (ri, rs, runlen))

    data = np.frombuffer(open(tgt, "rb").read(), dtype=np.uint8)
    for polarity, name in ((1, "1=잉크"), (0, "0=잉크")):
        bits = np.unpackbits(data)
        if polarity == 0:
            bits = 1 - bits
        cand = find_runs(bits, runlen)
        print("[%s] 연속 %d 후보 %d개" % (name, runlen, len(cand)))
        if len(cand) == 0:
            continue
        hits = 0
        W = len(rows[0])
        for c in cand[:4000]:
            row_start = int(c) - rs           # 이 행의 비트 시작
            for stride in list(range(W, 129)) + [256, 512]:
                ok = 0
                for i, r in enumerate(rows):
                    o = row_start + (i - ri) * stride
                    if o < 0 or o + W > len(bits):
                        break
                    seg = bits[o:o + W]
                    if np.array_equal(seg, np.array(r, dtype=np.uint8)):
                        ok += 1
                if ok >= max(6, len(rows) - 4):
                    print("   비트 0x%X (바이트 0x%08X.%d) stride=%d  %d/%d 행"
                          % (row_start, base + row_start // 8, row_start % 8, stride, ok, len(rows)))
                    hits += 1
                    if hits > 15:
                        return
        if not hits:
            print("   행 정렬 일치 없음")


if __name__ == "__main__":
    main()
