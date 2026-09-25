# -*- coding: utf-8 -*-
"""디코드한 글리프를 «질의»로 원본 폰트 데이터를 역검색한다.

1단계: 무압축 가정 — 여러 패킹(2bpp/1bpp, 비트순서, 값 반전, 행 폭)으로
       바이트열을 만들어 그대로 검색.
2단계: 행 단위 «임의 stride» 검색 — 행 사이 간격을 모를 때(패딩·인터리브) 쓴다.
       각 행 마스크가 stride 간격으로 연속 등장하는 위치를 찾는다.
"""
import sys

import numpy as np

from glyph_extract import glyphs


def pack_2bpp(g, row_bytes, msb_first, invert):
    out = bytearray()
    for row in g:
        acc = bytearray(row_bytes)
        for x, v in enumerate(row):
            if invert:
                v = 3 - v if v else 0
            bi, sh = x >> 2, (x & 3)
            shift = (3 - sh) * 2 if msb_first else sh * 2
            acc[bi] |= (v & 3) << shift
        out += acc
    return bytes(out)


def pack_1bpp(g, row_bytes, msb_first):
    out = bytearray()
    for row in g:
        acc = bytearray(row_bytes)
        for x, v in enumerate(row):
            if v:
                bi, sh = x >> 3, (x & 7)
                acc[bi] |= 1 << ((7 - sh) if msb_first else sh)
        out += acc
    return bytes(out)


def find_all(data, pat, limit=8):
    hits = []
    i = data.find(pat)
    while i >= 0 and len(hits) < limit:
        hits.append(i)
        i = data.find(pat, i + 1)
    return hits


def stage1(g, targets):
    print("=== 1단계: 무압축 패킹 직접 검색 ===")
    pats = {}
    for rb in (7, 8):
        for msb in (True, False):
            for inv in (False, True):
                pats["2bpp rb=%d %s%s" % (rb, "MSB" if msb else "LSB", " inv" if inv else "")] = \
                    pack_2bpp(g, rb, msb, inv)
    for rb in (4, 5):
        for msb in (True, False):
            pats["1bpp rb=%d %s" % (rb, "MSB" if msb else "LSB")] = pack_1bpp(g, rb, msb)
    total = 0
    for name, data, base in targets:
        for pname, pat in pats.items():
            hits = find_all(data, pat)
            if hits:
                total += 1
                print("  %s / %s : %s" % (name, pname, ["0x%X" % (base + h) for h in hits]))
    if not total:
        print("  전부 0건 — 원본은 무압축 평문이 아니다(또는 다른 패킹).")


def stage2(g, name, data, base, row_bytes=4, msb=True, max_stride=256, min_rows=8):
    """행 마스크를 stride 간격으로 찾는다."""
    rows = []
    for row in g:
        v = 0
        for x, px in enumerate(row):
            if px:
                v |= 1 << ((row_bytes * 8 - 1) - x) if msb else 1 << x
        rows.append(v.to_bytes(row_bytes, "big"))
    arr = np.frombuffer(data, dtype=np.uint8)
    # 첫 «잉크 많은» 행을 앵커로
    anchor_i = max(range(len(rows)), key=lambda i: bin(int.from_bytes(rows[i], "big")).count("1"))
    anchor = rows[anchor_i]
    cand = np.where(np.all(np.stack([arr[i:len(arr) - row_bytes + 1 + i] == anchor[i]
                                     for i in range(row_bytes)]), axis=0))[0]
    print("=== 2단계: %s — 앵커 행 %d, 후보 위치 %d개 ===" % (name, anchor_i, len(cand)))
    found = 0
    for c in cand:
        for stride in range(row_bytes, max_stride + 1):
            start = int(c) - anchor_i * stride
            if start < 0:
                continue
            ok = 0
            for i, r in enumerate(rows):
                o = start + i * stride
                if o + row_bytes <= len(data) and bytes(arr[o:o + row_bytes]) == r:
                    ok += 1
            if ok >= min_rows:
                print("   0x%08X stride=%d  %d/%d 행 일치" % (base + start, stride, ok, len(rows)))
                found += 1
                if found > 20:
                    return
    if not found:
        print("   일치 없음")


if __name__ == "__main__":
    sp = sys.argv[1]
    data = open(sp, "rb").read()
    off, w, h, gi = int(sys.argv[2], 0), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    g = glyphs(data, off, w, h)[gi][1]
    targets = []
    for spec in sys.argv[6:]:
        p, _, b = spec.partition("@")
        targets.append((p.split("\\")[-1], open(p, "rb").read(), int(b, 0) if b else 0))
    stage1(g, targets)
    for name, d, base in targets:
        stage2(g, name, d, base)
