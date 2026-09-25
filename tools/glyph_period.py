# -*- coding: utf-8 -*-
"""1bpp 글리프 표 검출 — «위상 전수» 주기성 검사.

지문: 셀 높이 H, 행당 B 바이트인 1bpp 폰트는 글리프마다 첫 행·끝 행이 비는 경향이 있다.
따라서 글리프 크기 G=B*H 로 나눈 나머지 위치별 «0 바이트 비율»에 강한 주기가 생긴다.

앞서 쓴 타일 점수식과 달리 이 검사는 **모든 시작 위상**을 동시에 본다
(주기 위치별 통계라 시작점을 몰라도 된다).

판정: 어떤 위상 p 에서 0비율 >= zhi 인데 구간 전체 0비율은 <= zlo 이면 후보.
      (구간 전체가 0에 가까우면 그냥 빈 영역이므로 배제)
"""
import sys


def profile(data, base, span, G):
    """구간 [base, base+span) 에서 위치 mod G 별 0 바이트 비율."""
    cnt = [0] * G
    tot = [0] * G
    end = min(base + span, len(data))
    for i in range(base, end):
        p = (i - base) % G
        tot[p] += 1
        if data[i] == 0:
            cnt[p] += 1
    return [cnt[p] / tot[p] if tot[p] else 0.0 for p in range(G)]


def scan(data, B, H, span=0x8000, zhi=0.90, zlo=0.55, min_peaks=2):
    G = B * H
    hits = []
    for base in range(0, len(data) - span, span):
        blk = data[base:base + span]
        overall = blk.count(0) / len(blk)
        if overall > zlo or overall < 0.02:
            continue
        pr = profile(data, base, span, G)
        peaks = [p for p in range(G) if pr[p] >= zhi]
        # 첫 행·끝 행이 비는 지문이므로 peak 가 «행 경계»에 몰려야 한다
        rows = sorted(set(p // B for p in peaks))
        if len(peaks) >= min_peaks * B and len(rows) >= min_peaks:
            hits.append((base, overall, rows, max(pr)))
    return hits


def main():
    path = sys.argv[1]
    data = open(path, "rb").read()
    lo = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0
    hi = int(sys.argv[3], 0) if len(sys.argv) > 3 else len(data)
    data = data[lo:hi]
    print("%s [0x%X,0x%X)  %d B" % (path, lo, hi, len(data)))
    cells = [
        # (행당 바이트, 행 수, 이름)  — 1bpp
        (2, 16, "1bpp 16x16"), (1, 8, "1bpp 8x8"), (2, 12, "1bpp 12x12"),
        (1, 16, "1bpp 8x16"), (3, 24, "1bpp 24x24"), (2, 14, "1bpp 16x14"),
        # 4bpp (행당 = 폭/2)
        (8, 16, "4bpp 16x16"), (6, 12, "4bpp 12x12"), (12, 24, "4bpp 24x24"),
        (4, 8, "4bpp 8x8"), (8, 12, "4bpp 16x12"), (10, 20, "4bpp 20x20"),
        # 8bpp (행당 = 폭)
        (16, 16, "8bpp 16x16"), (12, 12, "8bpp 12x12"), (24, 24, "8bpp 24x24"),
        (8, 8, "8bpp 8x8"),
    ]
    for (B, H, name) in cells:
        hits = scan(data, B, H)
        if not hits:
            print("  %-6s 1bpp : 후보 없음" % name)
            continue
        print("  %-6s 1bpp : 후보 %d" % (name, len(hits)))
        for base, ov, rows, mx in hits[:12]:
            print("      0x%08X  전체0=%.2f  빈행=%s  최대위상0비율=%.2f"
                  % (lo + base, ov, rows, mx))


if __name__ == "__main__":
    main()
