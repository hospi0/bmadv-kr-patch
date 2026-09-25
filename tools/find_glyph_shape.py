# -*- coding: utf-8 -*-
"""글리프를 «0/비0 패턴»으로 찾는다 — 팔레트 값이 달라도 걸린다.

지금까지의 4bpp 검색은 인덱스가 0~3 이라고 가정했다. 디스크 폰트가 다른
팔레트 인덱스를 쓰면 전부 빗나간다. 그래서 값이 아니라 «어느 픽셀이 잉크인가»
(512비트 마스크)로 대조한다. 512비트 정확 일치는 극도로 선택적이다.

레이아웃 후보: 트위들 32x16 4bpp / 선형 4bpp 32x16 / 선형 4bpp 28x14 / 선형 2bpp 28x14.
"""
import sys

import numpy as np

from find_glyph_tex import morton
from glyph_extract import glyphs, ink


def layout_twid_4bpp():
    """반환: 길이 256 리스트, 각 바이트의 (하위니블 픽셀좌표, 상위니블 픽셀좌표)."""
    m = [[None, None] for _ in range(256)]
    for y in range(16):
        for x in range(32):
            s = morton(x, y, 4, False)
            m[s >> 1][s & 1] = (x, y)
    return m, 256


def layout_lin_4bpp(w, h):
    m = [[None, None] for _ in range((w * h) // 2)]
    for y in range(h):
        for x in range(w):
            i = y * w + x
            m[i >> 1][i & 1] = (x, y)
    return m, (w * h) // 2


LAYOUTS = {
    "twid32x16": layout_twid_4bpp(),
    "lin4bpp32x16": layout_lin_4bpp(32, 16),
    "lin4bpp28x14": layout_lin_4bpp(28, 14),
}


def masks_for(g, layout):
    """(반드시 0 인 바이트 인덱스, 반드시 비0 인 (바이트,니블) 목록)"""
    m, size = layout
    zero_bytes = []
    ink_pos = []
    for bi in range(size):
        lo, hi = m[bi]
        vlo = g[lo[1]][lo[0]] if lo and lo[1] < 14 and lo[0] < 28 else 0
        vhi = g[hi[1]][hi[0]] if hi and hi[1] < 14 and hi[0] < 28 else 0
        if vlo == 0 and vhi == 0:
            zero_bytes.append(bi)
        else:
            ink_pos.append((bi, bool(vlo), bool(vhi)))
    return zero_bytes, ink_pos, size


def search(data, zero_bytes, ink_pos, size, step=2):
    a = np.frombuffer(data, dtype=np.uint8)
    n = (len(a) - size) // step
    starts = np.arange(n, dtype=np.int64) * step
    mask = np.ones(n, dtype=bool)
    for bi in zero_bytes[:32]:
        mask &= a[starts + bi] == 0
        if mask.sum() == 0:
            return []
    cand = starts[mask]
    out = []
    for off in cand:
        o = int(off)
        blk = data[o:o + size]
        ok = True
        for bi in zero_bytes:
            if blk[bi]:
                ok = False
                break
        if not ok:
            continue
        for bi, need_lo, need_hi in ink_pos:
            b = blk[bi]
            if bool(b & 0xF) != need_lo or bool((b >> 4) & 0xF) != need_hi:
                ok = False
                break
        if ok:
            out.append(o)
    return out


def main():
    state, off, gi = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3])
    gl = glyphs(open(state, "rb").read(), off, 64, 64)
    targets = sys.argv[4:]
    for idx, (cell, g) in enumerate(gl):
        if gi >= 0 and idx != gi:
            continue
        if ink(g) < 8:
            continue
        for lname, layout in LAYOUTS.items():
            zb, ip, size = masks_for(g, layout)
            print("글리프%d %s : 0바이트 %d개 / 잉크바이트 %d개 / 블록 %d B"
                  % (idx, lname, len(zb), len(ip), size))
            for t in targets:
                d = open(t, "rb").read()
                hits = search(d, zb, ip, size)
                if hits:
                    print("   ★ %s → %s" % (t.split("\\")[-1], ["0x%X" % h for h in hits[:8]]))


if __name__ == "__main__":
    main()
