# -*- coding: utf-8 -*-
"""괄호 «9쌍»의 좌우대칭을 지문으로 폰트 표를 찾는다 (포맷·인코딩 무관).

JIS 구1(= 우리 인덱스 T-0x40, lead 0x81)의 괄호쌍은 전부 좌우 반전이라
비트맵이 어떤 포맷이든 **잉크(팝카운트)가 같아야 한다.**

  （41 ）42 · 〔43 〕44 · ［45 ］46 · ｛47 ｝48 · 〈49 〉50
  《51 》52 · 「53 」54 · 『55 』56 · 【57 】58

9쌍이 동시에 맞을 확률은 극히 낮으므로 오탐이 거의 없다.
추가로 `痛`3114 가 괄호보다 조밀한지, 표가 촘촘한지만 본다.
(⚠️ 「인덱스 0 = 공백」 가정은 쓰지 않는다 — 이 가정 때문에 앞선 검색이 막혔을 수 있다.)
"""
import sys

import numpy as np

POPTAB = np.array([bin(i).count("1") for i in range(256)], dtype=np.int32)
PAIRS = [(41, 42), (43, 44), (45, 46), (47, 48), (49, 50),
         (51, 52), (53, 54), (55, 56), (57, 58)]
SAMPLES = list(range(60, 3100, 101))


def scan(data, K, need_pairs=7, step=1):
    a = np.frombuffer(data, dtype=np.uint8)
    cum = np.concatenate(([0], np.cumsum(POPTAB[a], dtype=np.int64)))
    arr = cum[K:] - cum[:-K]
    m = len(arr) - 3115 * K
    if m <= 0:
        return []
    B = np.arange(0, m, step, dtype=np.int64)

    def at(i):
        return arr[B + i * K]

    good = np.zeros(len(B), dtype=np.int32)
    nonzero = np.ones(len(B), dtype=bool)
    for lo, hi in PAIRS:
        pl, ph = at(lo), at(hi)
        good += (np.abs(pl - ph) <= 1) & (pl > 0)
        nonzero &= pl > 0
    ok = (good >= need_pairs) & nonzero
    if not ok.any():
        return []
    bits = K * 8
    p3114 = at(3114)
    p41 = at(41)
    # 괄호는 «얇은 획» — 셀의 12% 를 넘을 수 없다. 한자는 그보다 훨씬 조밀하다.
    ok &= (p41 < bits * 0.12) & (p41 > bits * 0.005)
    ok &= (p3114 > bits * 0.10) & (p3114 < bits * 0.55)
    ok &= p3114 > p41 * 2.0
    if not ok.any():
        return []
    filled = np.zeros(len(B), dtype=np.int32)
    for i in SAMPLES:
        filled += (at(i) > 0)
    ok &= filled >= int(len(SAMPLES) * 0.9)
    idx = np.flatnonzero(ok)
    return [(int(B[j]), K, int(good[j]), int(p41[j]), int(p3114[j])) for j in idx]


def main():
    path = sys.argv[1]
    sizes = ([int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2
             else list(range(32, 300, 2)))
    step = int(sys.argv[3], 0) if len(sys.argv) > 3 else 1
    data = open(path, "rb").read()
    out = []
    for K in sizes:
        out += scan(data, K, step=step)
    print("%s : 후보 %d" % (path.split("\\")[-1], len(out)))
    out.sort(key=lambda r: (-r[2], -r[4]))
    for B, K, g, p41, p3114 in out[:30]:
        print("   K=%-4d B=0x%08X  대칭쌍 %d/9  ink(（)=%-4d ink(痛)=%-5d" % (K, B, g, p41, p3114))


if __name__ == "__main__":
    main()
