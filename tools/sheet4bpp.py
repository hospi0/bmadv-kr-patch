# -*- coding: utf-8 -*-
"""한 구간을 여러 폭으로 4bpp(또는 2bpp) 렌더해 대조 시트로 만든다 — 폭 찾기용."""
import sys

from PIL import Image

src, lo, hi, out = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0), sys.argv[4]
widths = [int(x) for x in sys.argv[5].split(",")]
bpp = int(sys.argv[6]) if len(sys.argv) > 6 else 4
SCALE = int(sys.argv[7]) if len(sys.argv) > 7 else 3

data = open(src, "rb").read()[lo:hi]
ppb = 8 // bpp
maxv = (1 << bpp) - 1
# 니블/픽셀 펼치기
raw_hi = bytearray()
raw_lo = bytearray()
for byte in data:
    for k in range(ppb):
        raw_hi.append((byte >> ((ppb - 1 - k) * bpp)) & maxv)   # 상위 니블부터
        raw_lo.append((byte >> (k * bpp)) & maxv)               # 하위 니블부터
# 실제로 쓰인 최대값으로 정규화 (인덱스 0~3 만 쓰면 15로 나누면 거의 검게 나온다)
vmax = max(1, max(raw_hi))
print("사용된 최대 인덱스 = %d (0~%d 중)" % (vmax, maxv))
px_lo = bytes(min(255, v * 255 // vmax) for v in raw_hi)
px2 = bytes(min(255, v * 255 // vmax) for v in raw_lo)

panels = []
for order, buf in (("hi", px_lo), ("lo", bytes(px2))):
    for w in widths:
        h = min(len(buf) // w, 200)
        im = Image.frombytes("L", (w, h), buf[:w * h])
        panels.append(("%s w=%d" % (order, w), im.resize((w * SCALE, h * SCALE), Image.NEAREST)))

W = max(im.width for _, im in panels) + 16
H = sum(im.height + 14 for _, im in panels) + 8
sheet = Image.new("L", (W, H), 40)
y = 4
for lab, im in panels:
    sheet.paste(im, (8, y))
    y += im.height + 14
sheet.save(out)
print("→ %s  패널 %s" % (out, [p[0] for p in panels]))
