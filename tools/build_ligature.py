# -*- coding: utf-8 -*-
"""★합자(合字) 글리프 교체 — `（消費ＡＰＮ）` 표시.

이 게임은 「（消」「費」「ＡＰ」「１）」…을 **한 글리프 칸에 두 글자씩 압축해 그려**
그리스 문자 슬롯(Α~Θ)에 넣어 두었다. 그래서 SCENARIO 의 문자열에는
`ΑΒΓΖ` 처럼 보이고, `消費` 라는 문자열은 디스크·RAM 어디에도 없다
(평문·swap16·글리프 인덱스 전부 0건 — 텍스트 검색으로는 절대 못 찾는다).

  Α(839F) = `（` + `消`      → `（` + `소`
  Β(83A0) = `費`             → `모`
  Γ(83A1) = `ＡＰ`           → 그대로(영문)
  Δ~Θ(83A2~83A6) = `１）`~`５）` → 그대로(숫자)

즉 Α·Β 두 칸만 다시 그리면 화면이 `（소모ＡＰ３）` 이 된다.
⚠️ 원본 `（` 획은 그대로 두고 한자 자리만 덮는다.
"""
import os
import sys

import mfdfont as F
from hangul_raster import Rasterizer

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "work", "disc1")
BUILD = os.path.join(ROOT, "work", "build")

# (슬롯 문자, 덮을 열 범위, 넣을 한글)
JOBS = [
    ("Α", 9, 31, "소"),
    ("Β", 0, 27, "모"),
]


def paste(dst, src, x0, x1):
    """src 글리프의 잉크를 dst 의 [x0,x1) 구간에 가운데 정렬로 복사."""
    xs = [x for row in src for x, v in enumerate(row) if v]
    if not xs:
        return
    lo, hi = min(xs), max(xs)
    w = hi - lo + 1
    off = x0 + ((x1 - x0) - w) // 2 - lo
    for y in range(16):
        for x in range(x0, x1):
            dst[y][x] = 0
    for y, row in enumerate(src):
        for x, v in enumerate(row):
            if not v:
                continue
            nx = x + off
            if x0 <= nx < x1:
                dst[y][nx] = v


def main():
    target = os.path.join(BUILD, "SYSTEM.DAT")
    if not os.path.exists(target):
        raise SystemExit("work/build/SYSTEM.DAT 이 없다 — build_all_text.py 를 먼저 돌릴 것")
    data = bytearray(open(target, "rb").read())
    orig_len = len(data)
    # ⚠️ 합자 칸은 «두 글자를 압축해» 넣은 자리라 한자 자체가 가로로 눌려 있다.
    #    본문용 xscale=2 로 그리면 22px 짜리 글자가 되어 뭉개진다 — 여기서는 1배.
    r = Rasterizer(xscale=1)
    for ch, x0, x1, ko in JOBS:
        code = int.from_bytes(ch.encode("cp932"), "big")
        idx = F.sjis_to_index(code)
        bm = [row[:] for row in F.read_glyph(data, idx)]
        g = r.glyph(ko)
        if g is None:
            raise SystemExit("폰트에 없는 음절: %s" % ko)
        paste(bm, g, x0, x1)
        F.write_glyph(data, idx, bm)
        print("  %s(%04X idx=%d) 열 %d~%d ← '%s'" % (ch, code, idx, x0, x1 - 1, ko))
    if len(data) != orig_len:
        raise SystemExit("크기가 변했다")
    open(target, "wb").write(data)
    print("SYSTEM.DAT 합자 글리프 %d칸 교체 (크기 불변 %d)" % (len(JOBS), len(data)))


if __name__ == "__main__":
    main()
