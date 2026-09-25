# -*- coding: utf-8 -*-
"""Flycast(RetroArch) 세이브스테이트 안에서 메모리 블록 위치를 확정한다.

방법: 디스크의 1ST_READ.BIN 이 그대로 적재된 구간을 찾아 «메인 RAM 시작»을 앵커로 잡고,
앞뒤 구간의 성질(0 비율·엔트로피)로 다른 블록 경계를 관측한다. 추측하지 않고 실측한다.
"""
import collections
import math
import sys

STATE = sys.argv[1]
EXE = sys.argv[2] if len(sys.argv) > 2 else r"..\work\disc1\1ST_READ.BIN"

st = open(STATE, "rb").read()
exe = open(EXE, "rb").read()

# 앵커: 1ST_READ.BIN 선두 256바이트가 통째로 나오는 곳
anchor = st.find(exe[:256])
print("state size : 0x%X (%d)" % (len(st), len(st)))
print("exe[:256] 앵커 : 0x%X" % anchor)

# 얼마나 길게 일치하는가 (적재 후 코드가 자기수정할 수 있으므로 불일치 허용)
if anchor >= 0:
    same = sum(1 for i in range(len(exe)) if anchor + i < len(st) and st[anchor + i] == exe[i])
    print("1ST_READ.BIN %d B 중 %d B 일치 (%.2f%%)" % (len(exe), same, 100.0 * same / len(exe)))
    ram_base = anchor - 0x10000   # 1ST_READ.BIN 은 0x8C010000 에 적재 → RAM 시작은 -0x10000
    print("→ 메인 RAM 시작(가정 0x8C010000 적재) : 0x%X, 끝(16MB) : 0x%X"
          % (ram_base, ram_base + 0x1000000))
    print("   RAM 앞 구간 : 0x0 ~ 0x%X (%.2f MB)" % (ram_base, ram_base / 1048576.0))
    print("   RAM 뒤 구간 : 0x%X ~ 0x%X (%.2f MB)"
          % (ram_base + 0x1000000, len(st), (len(st) - ram_base - 0x1000000) / 1048576.0))

# 1MB 구간별 성질
print()
print("%-12s %-8s %-8s %s" % ("offset", "zero%", "entropy", "bar"))
MB = 1 << 20
for off in range(0, len(st), MB):
    blk = st[off:off + MB]
    z = blk.count(0) / len(blk)
    c = collections.Counter(blk[::7])
    n = len(blk[::7])
    ent = -sum(v / n * math.log2(v / n) for v in c.values())
    print("0x%08X   %6.2f   %6.3f  %s" % (off, z * 100, ent, "#" * int(ent * 4)))
