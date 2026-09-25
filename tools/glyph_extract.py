# -*- coding: utf-8 -*-
"""글리프 캐시 텍스처에서 글자 비트맵을 뽑는다 (원본 폰트 역검색용 오라클).

확정 파라미터(§10.8): 4bpp 트위들 y-low, 칸 32x16, 글리프 28x14, 인덱스 0~3.
"""
import sys

from find_glyph_tex import decode

CELL_W, CELL_H = 32, 16
GW, GH = 28, 14


def glyphs(data, off, tex_w, tex_h):
    px = decode(data, off, tex_w, tex_h, False)
    out = []
    for cy in range(tex_h // CELL_H):
        for cx in range(tex_w // CELL_W):
            g = [[px[(cy * CELL_H + y) * tex_w + cx * CELL_W + x] for x in range(GW)]
                 for y in range(GH)]
            out.append(((cx, cy), g))
    return out


def art(g):
    ch = " .+#"
    return "\n".join("".join(ch[v] for v in row) for row in g)


def ink(g):
    return sum(1 for row in g for v in row if v)


if __name__ == "__main__":
    path, off, w, h = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3]), int(sys.argv[4])
    data = open(path, "rb").read()
    for i, ((cx, cy), g) in enumerate(glyphs(data, off, w, h)):
        if ink(g) < 8:
            print("[%d] 칸(%d,%d) 빈 칸" % (i, cx, cy))
            continue
        print("[%d] 칸(%d,%d) 잉크 %d" % (i, cx, cy, ink(g)))
        print(art(g))
        print()
