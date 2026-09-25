# -*- coding: utf-8 -*-
"""1bpp 글리프 후보 탐색 (후보 생성용 휴리스틱, 확정 아님).

가정: 정방 글리프가 행당 (w/8) 바이트로 연속 저장된다.
점수: 타일 안에서 (a) 첫/끝 행이 비고 (b) 가운데 행에 픽셀이 있고
      (c) 전체 채움률이 0.1~0.6 인 타일의 비율.
"""
import sys


def score_block(data, off, w, h, ntiles=64):
    row = w // 8
    tile = row * h
    good = 0
    for t in range(ntiles):
        base = off + t * tile
        if base + tile > len(data):
            return 0.0
        rows = [int.from_bytes(data[base + r * row:base + (r + 1) * row], "big") for r in range(h)]
        bits = sum(bin(r).count("1") for r in rows)
        fill = bits / (w * h)
        if not (0.06 <= fill <= 0.55):
            continue
        if rows[0] != 0 or rows[-1] != 0:
            continue
        if rows[h // 2] == 0:
            continue
        good += 1
    return good / ntiles


def main(path, w, h, step=None, top=25):
    data = open(path, "rb").read()
    tile = (w // 8) * h
    step = step or tile
    best = []
    span = tile * 64
    for off in range(0, len(data) - span, step * 16):
        s = score_block(data, off, w, h)
        if s >= 0.5:
            best.append((s, off))
    best.sort(reverse=True)
    print("%s  %dx%d 1bpp  candidates=%d" % (path, w, h, len(best)))
    # 연속 구간으로 묶기
    merged = []
    for s, off in sorted(best, key=lambda x: x[1]):
        if merged and off - merged[-1][1] <= step * 32:
            merged[-1][1] = off
            merged[-1][2] = max(merged[-1][2], s)
        else:
            merged.append([off, off, s])
    for a, b, s in sorted(merged, key=lambda m: -(m[1] - m[0]))[:top]:
        print("  0x%08X - 0x%08X  span=%-9d best=%.2f" % (a, b, b - a, s))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
