# -*- coding: utf-8 -*-
"""글리프 캐시 텍스처의 «시작 오프셋 + 트위들 비트순서»를 전수 탐색으로 확정한다.

판정 근거(추측 아님): TA 디스플레이 리스트에서 읽은 UV 로
  64x64 텍스처 = 32x16 칸에 28x14 글리프 8개
가 확정됐다. 따라서 올바른 디코드라면 칸 안의
  열 28..31, 행 14..15 (= 패딩)
가 전부 0이어야 한다. 이 조건의 충족률을 점수로 쓴다.
"""
import sys


def morton(x, y, bits, xlow):
    v = 0
    for i in range(bits):
        if xlow:
            v |= ((x >> i) & 1) << (2 * i) | ((y >> i) & 1) << (2 * i + 1)
        else:
            v |= ((y >> i) & 1) << (2 * i) | ((x >> i) & 1) << (2 * i + 1)
    return v


def decode(data, off, w, h, xlow):
    bits = min(w, h).bit_length() - 1
    out = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            s = morton(x, y, bits, xlow)
            i = off + (s >> 1)
            if i >= len(data):
                return None
            byte = data[i]
            out[y * w + x] = (byte >> 4) & 0xF if (s & 1) else byte & 0xF
    return out


def score(px, w=64, h=64, cw=32, ch=16, gw=28, gh=14):
    """패딩 칸이 비어 있는 비율 − 글리프 칸이 비어 있으면 감점."""
    pad_total = pad_zero = 0
    ink = 0
    for cy in range(h // ch):
        for cx in range(w // cw):
            for y in range(ch):
                for x in range(cw):
                    v = px[(cy * ch + y) * w + cx * cw + x]
                    if x >= gw or y >= gh:
                        pad_total += 1
                        if v == 0:
                            pad_zero += 1
                    elif v:
                        ink += 1
    if not pad_total:
        return 0.0, 0
    return pad_zero / pad_total, ink


def main():
    path, lo, hi = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0)
    step = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0x40
    data = open(path, "rb").read()
    best = []
    for xlow in (True, False):
        for off in range(lo, hi, step):
            px = decode(data, off, 64, 64, xlow)
            if px is None or max(px) > 3 or max(px) == 0:
                continue
            s, ink = score(px)
            if ink < 200:
                continue
            best.append((s, ink, off, xlow))
    best.sort(reverse=True)
    print("후보 %d개 — 패딩공백률 높은 순" % len(best))
    for s, ink, off, xlow in best[:15]:
        print("  0x%08X  %s  패딩공백률=%.4f  잉크픽셀=%d"
              % (off, "x-low" if xlow else "y-low", s, ink))


if __name__ == "__main__":
    main()
