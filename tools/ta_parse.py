# -*- coding: utf-8 -*-
"""TA(타일 액셀러레이터) 디스플레이 리스트 파서.

32바이트 파라미터 스트림:
  PCW 상위 3비트 = 파라미터 종류. 4(0b100)=폴리곤/글로벌, 7(0b111)=정점.
  글로벌 파라미터: [PCW][ISP/TSP][TSP][TCW][...4워드]
  정점 파라미터:   [PCW][x f32][y f32][z f32][u f32][v f32][base color][offset color]
  정점 PCW 의 bit28 = 스트립 끝.

TCW: bit31 미프맵 / bit30 스캔순서(0=트위들) / bit29..27 픽셀포맷
     (0=1555 1=565 2=4444 3=YUV 4=범프 5=4bpp팔레트 6=8bpp팔레트)
     bit26 VQ / bit25..21 팔레트 선택 / bit20..0 주소(8바이트 단위)
"""
import struct
import sys

FMT = {0: "ARGB1555", 1: "RGB565", 2: "ARGB4444", 3: "YUV422",
       4: "Bump", 5: "4BPP_PAL", 6: "8BPP_PAL", 7: "resv"}


def decode_tcw(t):
    return dict(addr=(t & 0x1FFFFF) * 8, pal=(t >> 21) & 0x1F, vq=(t >> 26) & 1,
                fmt=FMT[(t >> 27) & 7], twiddled=not ((t >> 30) & 1), raw=t)


def parse(data, lo, hi, align_mod):
    """align_mod = 4바이트 정렬 위상(스테이트 오프셋 기준)."""
    # 스트림이 lo 기준 32바이트 격자에 있다고 가정하지 않는다 — 4바이트마다 훑는다.
    lo += (align_mod - lo) % 4
    groups = []
    cur = None
    off = lo
    while off + 32 <= hi:
        pcw = struct.unpack_from("<I", data, off)[0]
        typ = pcw >> 29
        if typ == 4 and (pcw & 0x00FF0000) == 0x008C0000:
            # 폴리곤 헤더 후보: PCW 하위에 텍스처/그로 셰이딩 비트가 선 형태
            tcw = struct.unpack_from("<I", data, off + 12)[0]
            cur = dict(off=off, pcw=pcw, tcw=decode_tcw(tcw), verts=[])
            groups.append(cur)
            off += 32
            continue
        if typ == 7 and cur is not None and (pcw & 0x0FFFFFFF) == 0:
            x, y, z, u, v = struct.unpack_from("<5f", data, off + 4)
            cur["verts"].append((x, y, u, v))
            off += 32
            continue
        off += 4
    return groups


if __name__ == "__main__":
    path, lo, hi = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0)
    amod = int(sys.argv[4], 0) if len(sys.argv) > 4 else 3
    ymin = float(sys.argv[5]) if len(sys.argv) > 5 else -1e9
    ymax = float(sys.argv[6]) if len(sys.argv) > 6 else 1e9
    data = open(path, "rb").read()
    gs = parse(data, lo, hi, amod)
    print("폴리곤 그룹 %d개" % len(gs))
    for g in gs:
        vs = [v for v in g["verts"] if -100 < v[0] < 1000 and -100 < v[1] < 1000]
        if not vs:
            continue
        ys = [v[1] for v in vs]
        if max(ys) < ymin or min(ys) > ymax:
            continue
        xs = [v[0] for v in vs]
        us = sorted(set(round(v[2], 4) for v in vs))
        vv = sorted(set(round(v[3], 4) for v in vs))
        t = g["tcw"]
        print("  0x%08X 정점%-3d x[%.0f..%.0f] y[%.0f..%.0f]  tex=0x%06X %s %s pal=%d"
              % (g["off"], len(vs), min(xs), max(xs), min(ys), max(ys),
                 t["addr"], t["fmt"], "twiddled" if t["twiddled"] else "linear", t["pal"]))
        print("        u=%s  v=%s" % (us[:6], vv[:6]))
