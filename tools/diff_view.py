# -*- coding: utf-8 -*-
"""두 스테이트의 «다른 바이트» 자체를 여러 폭으로 그려 배치를 읽는다.

대조군(대사 하나만 다름)에서 텍스트 비트맵이라면 어떤 폭에서 글자 모양이 드러난다.
"""
import sys

from PIL import Image

A, B, lo, hi, out = sys.argv[1], sys.argv[2], int(sys.argv[3], 0), int(sys.argv[4], 0), sys.argv[5]
widths = [int(x) for x in sys.argv[6].split(",")] if len(sys.argv) > 6 else [64, 128, 256, 320, 512, 640]
SCALE = 2

a = open(A, "rb").read()[lo:hi]
b = open(B, "rb").read()[lo:hi]
mask = bytes(255 if a[i] != b[i] else 0 for i in range(len(a)))

panels = []
for w in widths:
    h = len(mask) // w
    im = Image.frombytes("L", (w, h), mask[:w * h])
    im = im.resize((w * SCALE, h * SCALE), Image.NEAREST)
    panels.append((w, im))

pad = 8
W = max(im.width for _, im in panels) + pad * 2
H = sum(im.height + 20 for _, im in panels) + pad
sheet = Image.new("L", (W, H), 40)
y = pad
for w, im in panels:
    sheet.paste(im, (pad, y))
    y += im.height + 20
sheet.save(out)
print("차분 바이트 %d/%d  → %s  (폭 %s, %dx 확대)"
      % (sum(1 for v in mask if v), len(mask), out, widths, SCALE))
