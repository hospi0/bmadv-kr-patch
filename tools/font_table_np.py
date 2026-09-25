# -*- coding: utf-8 -*-
"""고정크기 폰트 표 탐색 — numpy 벡터화판.

핵심: 블록 팝카운트는 «누적합의 차»라서 시작 오프셋 전체에 대해 한 번에 구할 수 있고,
인덱스 i 블록의 팝카운트는 같은 배열을 i*K 만큼 민 것이다. B 전체를 동시에 판정한다.

제약(포맷 무관):
  0번 = 전각공백 → 팝카운트 0
  41 `（` 과 42 `）` 는 좌우대칭 → 팝카운트 일치(±2)
  3114 `痛` 조밀 / 1·5·9 `、・！` 희소·비어있지 않음
  표는 촘촘 (표본 인덱스 대부분 비어 있지 않음)
"""
import sys

import numpy as np

POPTAB = np.array([bin(i).count("1") for i in range(256)], dtype=np.int32)
SAMPLES = list(range(20, 3100, 97))


def scan(data, K, lo=0, hi=None):
    a = np.frombuffer(data, dtype=np.uint8)
    if hi is None:
        hi = len(a)
    cum = np.concatenate(([0], np.cumsum(POPTAB[a], dtype=np.int64)))
    n = len(a)
    if n < 3200 * K:
        return []
    arr = cum[K:] - cum[:-K]                 # arr[o] = 블록(o..o+K) 팝카운트
    m = len(arr) - 3115 * K
    if m <= 0:
        return []
    B = np.arange(lo, min(hi, m), 2, dtype=np.int64)

    def at(i):
        return arr[B + i * K]

    ok = at(0) == 0
    if not ok.any():
        return []
    p41, p42, p3114 = at(41), at(42), at(3114)
    bits = K * 8
    ok &= (p41 > 0) & (p42 > 0) & (np.abs(p41 - p42) <= 2)
    ok &= p3114 >= bits * 0.06
    for i in (1, 5, 9):
        p = at(i)
        ok &= (p > 0) & (p < p3114 * 0.7)
    if not ok.any():
        return []
    filled = np.zeros(len(B), dtype=np.int32)
    for i in SAMPLES:
        filled += (at(i) > 0)
    ok &= filled >= int(len(SAMPLES) * 0.95)
    idx = np.flatnonzero(ok)
    return [(int(B[j]), K, int(p41[j]), int(p42[j]), int(p3114[j])) for j in idx]


def main():
    path = sys.argv[1]
    lo = int(sys.argv[2], 0)
    hi = int(sys.argv[3], 0)
    ks = sys.argv[4] if len(sys.argv) > 4 else None
    data = open(path, "rb").read()[lo:hi]
    sizes = [int(x) for x in ks.split(",")] if ks else list(range(48, 292, 2))
    out = []
    for K in sizes:
        for r in scan(data, K):
            out.append(r)
    print("후보 %d" % len(out))
    out.sort(key=lambda r: -r[4])
    for B, K, a, b, c in out[:40]:
        print("   K=%-4d B=0x%08X (파일 0x%08X)  ink(41)=%-4d ink(42)=%-4d ink(痛)=%-5d"
              % (K, B, lo + B, a, b, c))


if __name__ == "__main__":
    main()
