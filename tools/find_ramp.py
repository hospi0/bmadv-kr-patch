# -*- coding: utf-8 -*-
"""u16 «1씩 증가하는 램프» 구간을 찾는다.

근거: 글리프 인덱스가 구1에서 `SJIS − 0x8140` 과 정확히 일치하므로,
사상이 표라면 표 앞부분은 0,1,2,3,… 항등 램프여야 한다.
"""
import sys

import numpy as np


def scan(path, min_len=40):
    data = open(path, "rb").read()
    for order in ("<u2", ">u2"):
        n = len(data) // 2
        a = np.frombuffer(data[:n * 2], dtype=order).astype(np.int64)
        d = np.diff(a)
        ok = d == 1
        idx = np.flatnonzero(np.concatenate(([True], ~ok, [True])))
        runs = np.diff(idx) - 1
        starts = idx[:-1]
        sel = np.flatnonzero(runs >= min_len)
        for s in sel:
            st = int(starts[s]) + 1
            ln = int(runs[s])
            print("  %s %s  0x%08X  길이 %d  시작값 %d → %d"
                  % (path.split("\\")[-1], order, st * 2, ln + 1, int(a[st]), int(a[st + ln])))


if __name__ == "__main__":
    for p in sys.argv[1:]:
        scan(p)
