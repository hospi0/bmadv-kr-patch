# -*- coding: utf-8 -*-
"""스테이트 앞구간(=RAM 이전)의 64KB 단위 밀도 프로파일 — 블록 경계를 «관측»으로 찾는다."""
import sys

path = sys.argv[1]
lo = int(sys.argv[2], 0)
hi = int(sys.argv[3], 0)
step = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0x10000
d = open(path, "rb").read()
run_start = None
prev_empty = None
for off in range(lo, hi, step):
    blk = d[off:off + step]
    nz = 1.0 - blk.count(0) / len(blk)
    empty = nz < 0.001
    if prev_empty is None or empty != prev_empty:
        if run_start is not None:
            print("0x%08X - 0x%08X  %8d B  %s" % (run_start, off, off - run_start,
                                                  "빈 구간" if prev_empty else "데이터"))
        run_start = off
        prev_empty = empty
print("0x%08X - 0x%08X  %8d B  %s" % (run_start, hi, hi - run_start,
                                      "빈 구간" if prev_empty else "데이터"))
