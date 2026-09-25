# -*- coding: utf-8 -*-
"""괄호쌍의 «행별» 대칭으로 폰트 표를 찾는다.

좌우 반전은 행 순서를 바꾸지 않고 행 «안»만 뒤집는다.
따라서 거울쌍은 **행마다 잉크 수가 같다.** 셀 높이 H, 행당 R=K/H 바이트라면
9쌍 × H행 = 최대 216개의 등식이 동시에 성립해야 한다 — 오탐이 사실상 남지 않는다.

포맷(1/2/4bpp)과 무관하다. 필요한 것은 K(글리프 바이트)와 H(행 수)뿐이다.
"""
import sys

import numpy as np

POPTAB = np.array([bin(i).count("1") for i in range(256)], dtype=np.int32)
PAIRS = [(41, 42), (43, 44), (45, 46), (47, 48), (49, 50),
         (51, 52), (53, 54), (55, 56), (57, 58)]


def scan(data, K, H, min_rows_frac=1.0, step=1):
    if K % H:
        return []
    R = K // H
    a = np.frombuffer(data, dtype=np.uint8)
    cum = np.concatenate(([0], np.cumsum(POPTAB[a], dtype=np.int64)))
    need = 3115 * K
    if len(a) < need + 16:
        return []
    m = len(a) - need
    B = np.arange(0, m, step, dtype=np.int64)

    def rowpop(base_idx, r):
        o = B + base_idx * K + r * R
        return cum[o + R] - cum[o]

    def glyphpop(i):
        o = B + i * K
        return cum[o + K] - cum[o]

    bits = K * 8
    p41 = glyphpop(41)
    p3114 = glyphpop(3114)
    ok = (p41 > bits * 0.01) & (p41 < bits * 0.12)
    ok &= (p3114 > bits * 0.10) & (p3114 < bits * 0.55) & (p3114 > p41 * 2.0)
    if not ok.any():
        return []
    match = np.zeros(len(B), dtype=np.int32)
    total = 0
    for lo, hi in PAIRS:
        for r in range(H):
            match += (rowpop(lo, r) == rowpop(hi, r))
            total += 1
    ok &= match >= int(total * min_rows_frac)
    idx = np.flatnonzero(ok)
    return [(int(B[j]), K, H, int(match[j]), total, int(p41[j]), int(p3114[j])) for j in idx]


def main():
    path = sys.argv[1]
    data = open(path, "rb").read()
    heights = [12, 14, 16, 20, 24, 28, 32]
    out = []
    for H in heights:
        for R in range(2, 17):
            K = R * H
            if K < 32 or K > 320:
                continue
            out += scan(data, K, H, min_rows_frac=1.0)
    print("%s : 완전일치 후보 %d" % (path.split("\\")[-1], len(out)))
    out.sort(key=lambda r: -r[6])
    for B, K, H, mt, tot, p41, p3114 in out[:30]:
        print("   K=%-4d H=%-3d R=%-3d B=0x%08X  행등식 %d/%d  ink(（)=%-4d ink(痛)=%-5d"
              % (K, H, K // H, B, mt, tot, p41, p3114))


if __name__ == "__main__":
    main()
