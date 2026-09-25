# -*- coding: utf-8 -*-
"""RAM 의 각 2KB 섹터가 «어느 디스크 파일»에서 왔는지 해시로 대조한다.

파일은 섹터 경계로 적재되므로 2048 정렬 창끼리 맞춰 본다.
어느 파일에도 없는 «비영 구간» = 런타임 생성/압축해제 데이터 → 폰트 후보.
"""
import hashlib
import os
import sys

SEC = 2048


def h(b):
    return hashlib.blake2b(b, digest_size=8).digest()


def build_index(ddir, skip=()):
    idx = {}
    for f in sorted(os.listdir(ddir)):
        if f in skip:
            continue
        p = os.path.join(ddir, f)
        if not os.path.isfile(p):
            continue
        d = open(p, "rb").read()
        for o in range(0, len(d) - SEC, SEC):
            blk = d[o:o + SEC]
            if blk.count(blk[:1]) == len(blk):
                continue                       # 단일 바이트 반복은 색인 안 함
            idx.setdefault(h(blk), (f, o))
        print("  색인 %-16s %10d B" % (f, len(d)), file=sys.stderr)
    return idx


def main():
    ram = open(sys.argv[1], "rb").read()
    base = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x8C000000
    ddir = sys.argv[3] if len(sys.argv) > 3 else os.path.join("..", "work", "disc1")
    idx = build_index(ddir)
    print("색인 창 %d개" % len(idx), file=sys.stderr)
    rows = []
    for o in range(0, len(ram) - SEC, SEC):
        blk = ram[o:o + SEC]
        if blk.count(blk[:1]) == len(blk):
            rows.append((o, "empty"))
            continue
        hit = idx.get(h(blk))
        rows.append((o, hit[0] if hit else "?"))
    runs = []
    for o, tag in rows:
        if runs and runs[-1][2] == tag:
            runs[-1][1] = o + SEC
        else:
            runs.append([o, o + SEC, tag])
    unknown = [r for r in runs if r[2] == "?"]
    print("전체 구간 %d개 / 미상 구간 %d개, 미상 총량 %d KB"
          % (len(runs), len(unknown), sum(r[1] - r[0] for r in unknown) // 1024))
    print("\n미상 구간 — 큰 순:")
    for a, b, t in sorted(unknown, key=lambda r: -(r[1] - r[0]))[:25]:
        print("   0x%08X - 0x%08X  %8d KB" % (base + a, base + b, (b - a) // 1024))
    print("\n파일별 적재 구간:")
    for a, b, t in runs:
        if t in ("?", "empty"):
            continue
        print("   0x%08X - 0x%08X  %8d KB   %s" % (base + a, base + b, (b - a) // 1024, t))


if __name__ == "__main__":
    main()
