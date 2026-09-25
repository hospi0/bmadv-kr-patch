# -*- coding: utf-8 -*-
"""최소 BDF 리더 — 픽셀 폰트는 TTF 래스터라이저를 거치지 않고 «BDF 직독» 한다.

TTF 로 렌더하면 힌팅·안티에일리어싱이 끼어들어 원본 픽셀이 뭉개진다.
BDF 는 비트맵이 그대로 들어 있으므로 손실이 없다.
"""
import sys


class BDF:
    def __init__(self, path):
        self.glyphs = {}          # codepoint -> dict(bbw,bbh,bbx,bby,dwidth,rows)
        self.fbbx = None
        cur = None
        bitmap = None
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.rstrip("\n").rstrip("\r")
                if bitmap is not None:
                    if line.startswith("ENDCHAR"):
                        cur["rows"] = bitmap
                        if cur.get("enc", -1) >= 0:
                            self.glyphs[cur["enc"]] = cur
                        cur = None
                        bitmap = None
                    else:
                        bitmap.append(line.strip())
                    continue
                if line.startswith("FONTBOUNDINGBOX"):
                    self.fbbx = [int(x) for x in line.split()[1:]]
                elif line.startswith("STARTCHAR"):
                    cur = {"enc": -1}
                elif line.startswith("ENCODING") and cur is not None:
                    cur["enc"] = int(line.split()[1])
                elif line.startswith("DWIDTH") and cur is not None:
                    cur["dwidth"] = int(line.split()[1])
                elif line.startswith("BBX") and cur is not None:
                    w, h, x, y = [int(v) for v in line.split()[1:5]]
                    cur["bbw"], cur["bbh"], cur["bbx"], cur["bby"] = w, h, x, y
                elif line.startswith("BITMAP") and cur is not None:
                    bitmap = []

    def bitmap(self, ch):
        """문자 → (w, h, xoff, yoff, dwidth, [[0/1]*w]*h). 없으면 None."""
        g = self.glyphs.get(ord(ch))
        if g is None:
            return None
        w, h = g["bbw"], g["bbh"]
        rows = []
        for line in g["rows"][:h]:
            if not line:
                rows.append([0] * w)
                continue
            v = int(line, 16)
            nbits = len(line) * 4
            rows.append([(v >> (nbits - 1 - i)) & 1 for i in range(w)])
        while len(rows) < h:
            rows.append([0] * w)
        return dict(w=w, h=h, x=g["bbx"], y=g["bby"], dwidth=g.get("dwidth", w), rows=rows)


if __name__ == "__main__":
    path = sys.argv[1]
    f = BDF(path)
    print("%s: 글리프 %d개, FONTBOUNDINGBOX=%s" % (path.split("\\")[-1], len(f.glyphs), f.fbbx))
    for ch in (sys.argv[2] if len(sys.argv) > 2 else "가힣안녕A"):
        b = f.bitmap(ch)
        if not b:
            print("  %s : 없음" % ch)
            continue
        print("  %s : %dx%d  x=%d y=%d dwidth=%d" % (ch, b["w"], b["h"], b["x"], b["y"], b["dwidth"]))
        for r in b["rows"]:
            print("     " + "".join("#" if v else "." for v in r))
