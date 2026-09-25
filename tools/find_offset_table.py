# -*- coding: utf-8 -*-
"""단조 증가 오프셋 표를 찾는다 (가변길이 글리프 폰트의 지문).

글리프 인덱스가 조밀한 순차 번호(`痛`=3114 등)로 확인됐으므로,
폰트가 압축·가변길이라면 인덱스로 색인하는 **단조 증가 오프셋 표**가 반드시 있다.
u16/u32 · LE/BE 를 모두 본다.
"""
import sys

import numpy as np


def scan(data, name, dtype, order, min_len=800):
    itemsize = np.dtype(dtype).itemsize
    n = len(data) // itemsize
    a = np.frombuffer(data[:n * itemsize], dtype=(">" if order == "BE" else "<") + dtype[-2:])
    d = np.diff(a.astype(np.int64))
    # «엄격히 증가» + 한 항목 증가폭이 글리프 하나 크기 정도
    ok = (d > 0) & (d <= 512)
    idx = np.flatnonzero(np.concatenate(([True], ~ok, [True])))
    runs = np.diff(idx) - 1
    starts = idx[:-1]
    sel = np.flatnonzero(runs >= min_len)
    out = []
    for s in sel:
        st = int(starts[s]) + 1
        ln = int(runs[s])
        if st + ln >= len(a):
            ln = len(a) - st - 1
        if ln < min_len:
            continue
        out.append((st * itemsize, ln, int(a[st]), int(a[st + ln])))
    if out:
        print("[%s %s %s] 단조 구간 %d개" % (name, dtype, order, len(out)))
        for off, ln, v0, v1 in sorted(out, key=lambda r: -r[1])[:6]:
            print("    파일 0x%08X  항목 %d개  %d → %d" % (off, ln, v0, v1))
    return out


def main():
    for path in sys.argv[1:]:
        data = open(path, "rb").read()
        name = path.split("\\")[-1]
        for dtype, order in (("u4", "LE"), ("u4", "BE"), ("u2", "LE"), ("u2", "BE")):
            scan(data, name, dtype, order)


if __name__ == "__main__":
    main()
