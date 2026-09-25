# -*- coding: utf-8 -*-
"""한글 → Black/Matrix Advanced 폰트 글리프(32×16, 2bpp) 래스터라이저.

설계 근거(실측):
  · 게임 글리프 셀 32×16, 실제 잉크는 대략 26×13.
  · 화면에서 세로만 2배로 늘어난다(렌더 공간 640×240 → 화면 640×480).
    즉 폰트 1픽셀 = 화면 1×2 픽셀.
  · 게임 원본 획은 «가로 2픽셀 / 세로 1픽셀» 이다(`痛` 등에서 확인).
  → 갈무리14(14×14, 획 1픽셀)를 **가로만 2배**로 늘리면 획이 가로 2·세로 1이 되어
    원본 일본어 글리프와 굵기·비율이 그대로 맞는다. 28×14 로 셀에 꼭 들어간다.

베이스라인은 셀 위에서 14행에 둔다(BDF 의 y 오프셋 기준). 잉크 값은 1(가장 진함).
"""
import sys

from bdf import BDF

CELL_W, CELL_H = 32, 16
BASELINE = 14          # 셀 위에서부터 몇 번째 행이 베이스라인인가
INK = 1                # 2bpp 값: 1 = 가장 진함(게임 본체 획과 동일)
DEFAULT_BDF = r"C:\claude\utils\font\Galmuri-v2.40.3\Galmuri14.bdf"


class Rasterizer:
    def __init__(self, bdf_path=DEFAULT_BDF, xscale=2, xshift=0, yshift=0):
        self.font = BDF(bdf_path)
        self.xscale = xscale
        self.xshift = xshift
        self.yshift = yshift

    def glyph(self, ch, ink=INK):
        """문자 → [16][32] 값(0~3). 폰트에 없으면 None."""
        b = self.font.bitmap(ch)
        if b is None:
            return None
        out = [[0] * CELL_W for _ in range(CELL_H)]
        top = BASELINE - (b["y"] + b["h"]) + self.yshift
        left = b["x"] * self.xscale + self.xshift
        for ry, row in enumerate(b["rows"]):
            cy = top + ry
            if not 0 <= cy < CELL_H:
                continue
            for rx, v in enumerate(row):
                if not v:
                    continue
                for k in range(self.xscale):
                    cx = left + rx * self.xscale + k
                    if 0 <= cx < CELL_W:
                        out[cy][cx] = ink
        return out

    def advance(self, ch):
        b = self.font.bitmap(ch)
        return None if b is None else b["dwidth"] * self.xscale


def art(bm, chars=" .+#"):
    return "\n".join("".join(chars[v] for v in row) for row in bm)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BDF
    text = sys.argv[2] if len(sys.argv) > 2 else "안녕가힣"
    r = Rasterizer(path)
    for ch in text:
        g = r.glyph(ch)
        if g is None:
            print("%s : 폰트에 없음" % ch)
            continue
        ink = sum(1 for row in g for v in row if v)
        print("=== %s  잉크 %d px ===" % (ch, ink))
        print(art(g))
