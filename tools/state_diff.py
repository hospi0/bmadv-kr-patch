# -*- coding: utf-8 -*-
"""두 스테이트의 차분 구간을 찾는다.

용법: state_diff.py A.bin B.bin [블록크기] [최대출력]
대조군(대사 하나만 다른 두 스테이트)에 쓰면 텍스트 렌더 경로만 남는다.
"""
import sys

a = open(sys.argv[1], "rb").read()
b = open(sys.argv[2], "rb").read()
BLK = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x400
LIMIT = int(sys.argv[4], 0) if len(sys.argv) > 4 else 60

print("A %d B / B %d B" % (len(a), len(b)))
n = min(len(a), len(b))
if len(a) != len(b):
    print("경고: 크기 다름")

# 블록 단위로 다른 곳 표시
diff_blocks = []
for off in range(0, n, BLK):
    ea = a[off:off + BLK]
    eb = b[off:off + BLK]
    if ea != eb:
        nd = sum(1 for i in range(len(ea)) if ea[i] != eb[i])
        diff_blocks.append((off, nd))

total_bytes = sum(d for _, d in diff_blocks)
print("다른 블록 %d개 (블록 %d B), 다른 바이트 %d개" % (len(diff_blocks), BLK, total_bytes))

# 연속 블록을 구간으로 합치기
runs = []
for off, nd in diff_blocks:
    if runs and off == runs[-1][1]:
        runs[-1][1] = off + BLK
        runs[-1][2] += nd
    else:
        runs.append([off, off + BLK, nd])
print("연속 구간 %d개 — 다른 바이트 많은 순:" % len(runs))
for s, e, nd in sorted(runs, key=lambda r: -r[2])[:LIMIT]:
    print("  0x%08X - 0x%08X  길이 %-8d 다른바이트 %-8d (%.1f%%)"
          % (s, e, e - s, nd, 100.0 * nd / (e - s)))
