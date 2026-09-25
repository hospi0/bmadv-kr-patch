# -*- coding: utf-8 -*-
"""괄호쌍 행별 거울 대조 — 2단 필터판(빠름).

1단(numpy, 전 오프셋): `（`41 과 `）`42 의 «글리프 전체» 잉크가 같고 얇을 것.
2단(파이썬, 생존자만): 9쌍 × H행 «행별» 잉크 등식 전수.

1단에서 대부분 죽으므로 2단 비용이 작다.
"""
import sys

import numpy as np

POPTAB = np.array([bin(i).count("1") for i in range(256)], dtype=np.int32)
PAIRS = [(41, 42), (43, 44), (45, 46), (47, 48), (49, 50),
         (51, 52), (53, 54), (55, 56), (57, 58)]


def run(data, combos, step=2, tol=0):
    a = np.frombuffer(data, dtype=np.uint8)
    cum = np.concatenate(([0], np.cumsum(POPTAB[a], dtype=np.int64)))
    results = []
    for K, H in combos:
        R = K // H
        if R * H != K:
            continue
        need = 3115 * K
        if len(a) < need + 16:
            continue
        m = len(a) - need
        B = np.arange(0, m, step, dtype=np.int64)
        bits = K * 8

        def gp(i):
            o = B + i * K
            return cum[o + K] - cum[o]

        p41, p42 = gp(41), gp(42)
        ok = (np.abs(p41 - p42) <= tol) & (p41 > bits * 0.015) & (p41 < bits * 0.11)
        p3114 = gp(3114)
        ok &= (p3114 > p41 * 2.2) & (p3114 > bits * 0.10) & (p3114 < bits * 0.55)
        idx = np.flatnonzero(ok)
        if len(idx) == 0:
            continue
        # 2단: 행별
        surv = []
        for j in idx:
            b0 = int(B[j])
            good = True
            for lo, hi in PAIRS:
                base_l = b0 + lo * K
                base_h = b0 + hi * K
                for r in range(H):
                    ol = base_l + r * R
                    oh = base_h + r * R
                    if (cum[ol + R] - cum[ol]) != (cum[oh + R] - cum[oh]):
                        good = False
                        break
                if not good:
                    break
            if good:
                surv.append((b0, K, H, int(p41[j]), int(p3114[j])))
        if surv:
            print("  K=%-4d H=%-3d : 1단 %6d → 2단 %d" % (K, H, len(idx), len(surv)))
        results += surv
    return results


if __name__ == "__main__":
    path = sys.argv[1]
    step = int(sys.argv[2], 0) if len(sys.argv) > 2 else 2
    combos = [(144, 24), (98, 14), (128, 16), (72, 12), (196, 28), (256, 32),
              (96, 16), (192, 24), (72, 24), (64, 16), (128, 32), (48, 16),
              (288, 24), (256, 16), (112, 14), (160, 20), (200, 20), (168, 24),
              (120, 24), (84, 14), (56, 14), (224, 28), (392, 28)]
    data = open(path, "rb").read()
    res = run(data, combos, step=step)
    print("%s : 최종 후보 %d" % (path.replace("\\", "/").split("/")[-1], len(res)))
    for B, K, H, p41, p3114 in sorted(res, key=lambda r: -r[4])[:25]:
        print("   K=%-4d H=%-3d R=%-3d B=0x%08X  ink(（)=%-4d ink(痛)=%-5d" % (K, H, K // H, B, p41, p3114))
