# -*- coding: utf-8 -*-
"""RAM 의 각 구간이 «어느 디스크 파일»에서 왔는지 대조한다.

목적: 대사 표시 시점에 적재돼 있는 파일 집합을 확정한다.
폰트는 압축된 채 상주할 것이므로, 그 압축 원본은 반드시 어느 파일 안에 있다.
"""
import os
import sys

STEP = 0x1000
PROBE = 48


def main():
    ram = open(sys.argv[1], "rb").read()
    base = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x8C000000
    ddir = sys.argv[3] if len(sys.argv) > 3 else os.path.join("..", "work", "disc1")
    files = {}
    for f in sorted(os.listdir(ddir)):
        if f.endswith((".DAT", ".BIN")):
            files[f] = open(os.path.join(ddir, f), "rb").read()
    print("대조 대상 파일 %d개: %s" % (len(files), ", ".join(files)))
    rows = []
    for off in range(0, len(ram) - PROBE, STEP):
        probe = ram[off:off + PROBE]
        if probe.count(probe[:1]) == len(probe):     # 단일 바이트 반복 = 정보 없음
            rows.append((off, None, None))
            continue
        hit = None
        for name, d in files.items():
            j = d.find(probe)
            if j >= 0:
                hit = (name, j)
                break
        rows.append((off, hit[0] if hit else "?", hit[1] if hit else None))
    # 같은 파일이 이어지는 구간으로 묶기
    runs = []
    for off, name, j in rows:
        if runs and runs[-1][2] == name:
            runs[-1][1] = off + STEP
        else:
            runs.append([off, off + STEP, name, j])
    for a, b, name, j in runs:
        if name is None:
            continue
        tag = "%s@0x%X" % (name, j) if j is not None else "미상"
        print("0x%08X - 0x%08X  %8d KB   %s" % (base + a, base + b, (b - a) // 1024, tag))


if __name__ == "__main__":
    main()
